import express, { Request, Response, NextFunction } from "express";
import http from "http";
import { WebSocketServer, WebSocket } from "ws";
import { randomUUID } from "crypto";

// ---------- Types ----------

interface DeviceHelloMessage {
  type: "hello";
  deviceId: string;
}

interface CommandMessage {
  type: "command";
  requestId: string;
  command: string;
  params: Record<string, unknown>;
}

interface DeviceResponseMessage {
  type: "response";
  requestId: string;
  status: "ok" | "error";
  result?: unknown;
  error?: string;
}

type IncomingDeviceMessage = DeviceHelloMessage | DeviceResponseMessage | any;

interface PendingRequest {
  resolve: (value: DeviceResponseMessage) => void;
  reject: (reason?: unknown) => void;
  timeout: NodeJS.Timeout;
}

// HTTP request from MATLAB
interface SendCommandBody {
  deviceId: string;
  command: string;
  params?: Record<string, unknown>;
}

// ---------- In-memory state (single instance only) ----------

// deviceId -> WebSocket
const deviceConnections = new Map<string, WebSocket>();

// requestId -> pending promise
const pendingRequests = new Map<string, PendingRequest>();

// deviceId -> last status (optional, for health/debug)
const deviceInfo = new Map<string, { status: string; lastSeen: number }>();

// ---------- Express app ----------

const app = express();

// Allow JSON bodies
app.use(express.json());

// Simple CORS (you can tighten this later)
app.use((req: Request, res: Response, next: NextFunction) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type,Authorization");
  if (req.method === "OPTIONS") {
    res.sendStatus(204);
  } else {
    next();
  }
});

// Health endpoint
app.get("/health", (req: Request, res: Response) => {
  res.json({
    status: "ok",
    devices: Array.from(deviceInfo.entries()).map(([deviceId, info]) => ({
      deviceId,
      status: info.status,
      lastSeen: info.lastSeen
    }))
  });
});

// HTTP POST /sendCommand  (MATLAB calls this)
app.post("/sendCommand", async (req: Request, res: Response) => {
  const body: SendCommandBody = req.body;

  if (!body || typeof body.deviceId !== "string" || typeof body.command !== "string") {
    return res.status(400).json({ status: "error", error: "Invalid payload" });
  }

  const deviceId = body.deviceId;
  const command = body.command;
  const params = body.params ?? {};

  const ws = deviceConnections.get(deviceId);
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    return res.status(503).json({
      status: "error",
      error: `Device ${deviceId} not connected`
    });
  }

  const requestId = randomUUID();

  // Create a promise for the response from the device
  const responsePromise = new Promise<DeviceResponseMessage>((resolve, reject) => {
    const timeoutMs = 5000; // 5 seconds

    const timeout = setTimeout(() => {
      pendingRequests.delete(requestId);
      reject(new Error("Timeout waiting for device response"));
    }, timeoutMs);

    pendingRequests.set(requestId, { resolve, reject, timeout });
  });

  const message: CommandMessage = {
    type: "command",
    requestId,
    command,
    params
  };

  try {
    ws.send(JSON.stringify(message));

    const response = await responsePromise;

    if (response.status === "ok") {
      return res.json({
        status: "ok",
        result: response.result
      });
    }
    return res.status(500).json({
      status: "error",
      error: response.error ?? "Device returned error"
    });
  } catch (err: any) {
    return res.status(504).json({
      status: "error",
      error: err?.message ?? "Gateway error"
    });
  }
});

// ---------- HTTP server + WebSocket server ----------

const port = Number(process.env.PORT) || 8080;
const server = http.createServer(app);

const wss = new WebSocketServer({ server, path: "/ws" });

wss.on("connection", (ws: WebSocket) => {
  let deviceId: string | null = null;
  console.log("[WS] Incoming connection");

  const handleClose = () => {
    if (deviceId) {
      console.log(`[WS] Device disconnected: ${deviceId}`);
      deviceConnections.delete(deviceId);
      deviceInfo.set(deviceId, {
        status: "disconnected",
        lastSeen: Date.now()
      });
    }
  };

  ws.on("message", (data: Buffer) => {
    try {
      const text = data.toString("utf-8");
      const msg: IncomingDeviceMessage = JSON.parse(text);

      if (!deviceId) {
        // Expect hello as the first message
        if (msg.type === "hello" && typeof msg.deviceId === "string") {
          deviceId = msg.deviceId;
          deviceConnections.set(msg.deviceId, ws);
          deviceInfo.set(msg.deviceId, { status: "connected", lastSeen: Date.now() });
          console.log(`[WS] Device connected: ${deviceId}`);
        } else {
          console.warn("[WS] First message not hello, closing");
          ws.close(1002, "Expected hello");
        }
        return;
      }

      // After hello, handle responses
      if (msg.type === "response") {
        const response = msg as DeviceResponseMessage;
        const { requestId } = response;

        if (requestId && pendingRequests.has(requestId)) {
          const pending = pendingRequests.get(requestId)!;
          clearTimeout(pending.timeout);
          pendingRequests.delete(requestId);
          pending.resolve(response);
        } else {
          console.warn(
            `[WS] Unknown or timed-out requestId=${requestId} from device=${deviceId}`
          );
        }

        deviceInfo.set(deviceId, { status: "connected", lastSeen: Date.now() });
      } else {
        // You can add telemetry handling here if needed
        console.log(`[WS] Unhandled message from ${deviceId}:`, msg);
      }
    } catch (e) {
      console.error("[WS] Error handling message:", e);
    }
  });

  ws.on("close", handleClose);
  ws.on("error", (err) => {
    console.error("[WS] Error:", err);
    handleClose();
  });
});

// Start server
server.listen(port, () => {
  console.log(`Gateway listening on port ${port}`);
});
