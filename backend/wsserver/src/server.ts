import express, { Request, Response, NextFunction } from "express";
import http from "http";
import { WebSocketServer, WebSocket } from "ws";
import { DeviceCommandAckMessage, CommandRequest, GetConfigRequest, IncomingDeviceMessage, DeviceSetConfigMessage } from "./types";

// ---------- Types ----------

interface PendingRequest {
  resolve: (value: DeviceCommandAckMessage) => void;
  reject: (reason?: unknown) => void;
  timeout: NodeJS.Timeout;
}

interface DeviceInfo {
    status: string;
    lastSeen: number;
    config?: any;
}

// ---------- In-memory state (single instance only) ----------

// deviceId -> WebSocket
const deviceConnections = new Map<string, WebSocket>();

// requestId -> pending promise
const pendingRequests = new Map<string, PendingRequest>();

// deviceId -> last status (optional, for health/debug)
const deviceInfo = new Map<string, DeviceInfo>();

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
      lastSeen: info.lastSeen,
      config: info.config
    }))
  });
});

// HTTP POST /sendCommand  remote calls this
app.post("/sendCommand", async (req: Request, res: Response) => {
  const body: CommandRequest = req.body;

  if (!body || typeof body.deviceId !== "string" || typeof body.commandId !== "string") {
    return res.status(400).json({ status: "error", error: "Invalid payload" });
  }

  const deviceId = body.deviceId;
  const commandId = body.commandId;

  const ws = deviceConnections.get(deviceId);
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    return res.status(503).json({
      status: "error",
      error: `Device ${deviceId} not connected`
    });
  }

  // Create a promise for the response from the device
  const responsePromise = new Promise<DeviceCommandAckMessage>((resolve, reject) => {
    const timeoutMs = 5000; // 5 seconds

    const timeout = setTimeout(() => {
      pendingRequests.delete(commandId);
      reject(new Error("Timeout waiting for device response"));
    }, timeoutMs);

    pendingRequests.set(commandId, { resolve, reject, timeout });
  });

  try {
    ws.send(JSON.stringify(body));

    const response = await responsePromise;

    if (response.status === "ok") {
      return res.json({
        status: "ok",
        result: response.response
      });
    }
    return res.status(500).json({
      status: "error",
      error: "Device returned error"
    });
  } catch (err: any) {
    return res.status(504).json({
      status: "error",
      error: err?.message ?? "Gateway error"
    });
  }
});

// HTTP POST /getConfig
app.post("/getConfig", (req: Request, res: Response) => {
  const body: GetConfigRequest = req.body;

  if (!body || typeof body.deviceId !== "string") {
    return res.status(400).json({ status: "error", error: "Invalid payload" });
  }

  const deviceId = body.deviceId;
  const deviceInfoEntry = deviceInfo.get(deviceId);

  if (!deviceInfoEntry) {
    return res.status(404).json({
      status: "error",
      error: `Device ${deviceId} not found`
    });
  }

  if (deviceInfoEntry.config === undefined || deviceInfoEntry.config === null) {
    return res.status(404).json({
      status: "error",
      error: `Configuration not found for device ${deviceId}`
    });
  }

  return res.json({
    status: "ok",
    config: deviceInfoEntry.config
  });
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
        if (msg.type === "ack") {
            const response = msg as DeviceCommandAckMessage;
            const { commandId } = response;
            if (commandId && pendingRequests.has(commandId)) {
                const pending = pendingRequests.get(commandId)!;
                clearTimeout(pending.timeout);
                pendingRequests.delete(commandId);
                pending.resolve(response);
            }
            deviceInfo.set(deviceId, { status: "connected", lastSeen: Date.now() });
        } else if (msg.type === "setConfig") {
          const setConfig = msg as DeviceSetConfigMessage;
          deviceInfo.set(deviceId, { status: "connected", lastSeen: Date.now(), config: setConfig.config });
        } else {
            console.warn("[WS] Unhandled message type:", msg.type);
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
