import {onRequest} from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import {getFirestore} from "firebase-admin/firestore";

interface CommandData {
  deviceId: string;
  commandId: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  command: any; // The actual command payload
  timestamp?: number;
}

interface AckData {
  deviceId: string;
  commandId: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  response: any; // The response payload from the device
  timestamp?: number;
}

export const sendCommand = onRequest(async (request, response) => {
  // Set CORS headers to allow cross-origin requests
  response.set("Access-Control-Allow-Origin", "*");
  response.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  response.set("Access-Control-Allow-Headers", "Content-Type");

  // Handle preflight OPTIONS request
  if (request.method === "OPTIONS") {
    response.status(200).send("");
    return;
  }

  try {
    // Only allow POST requests
    if (request.method !== "POST") {
      response.status(405).json({
        error: "Method not allowed. Only POST requests are supported.",
      });
      return;
    }

    // Extract command data from request body
    const {deviceId, commandId, command}: CommandData = request.body;

    if (!deviceId || !commandId || !command) {
      response.status(400).json({
        error: "Missing required parameters: deviceId, commandId, and command",
      });
      return;
    }

    logger.info(`Sending command ${commandId} to device ${deviceId}`);

    // Initialize Firestore
    const db = getFirestore();

    // Create the command document
    const commandData: CommandData = {
      deviceId,
      commandId,
      command,
      timestamp: Date.now(),
    };

    // Write command to Firestore in the commands collection
    await db
      .collection("commands")
      .doc(deviceId)
      .collection("commands")
      .doc(commandId)
      .set(commandData);

    logger.info(`Command ${commandId} written for device ${deviceId}`);

    // Wait for acknowledgement using real-time listener
    const timeoutMs = 30000; // 30 seconds timeout
    const ackDocRef = db
      .collection("acks")
      .doc(deviceId)
      .collection("acks")
      .doc(commandId);

    // Create a promise that resolves when the acknowledgement is received
    const waitForAck = new Promise<AckData>((resolve, reject) => {
      let unsubscribe: (() => void) | null = null;

      // Set up timeout
      const timeoutId = setTimeout(() => {
        if (unsubscribe) {
          unsubscribe();
        }
        reject(new Error("Timeout waiting for device acknowledgement"));
      }, timeoutMs);

      // Set up real-time listener
      unsubscribe = ackDocRef.onSnapshot(
        (doc) => {
          if (doc.exists) {
            const ackData = doc.data() as AckData;
            logger.info(
              `Ack rx for command ${commandId} from device ${deviceId}`
            );

            // Clean up
            clearTimeout(timeoutId);
            if (unsubscribe) {
              unsubscribe();
            }

            resolve(ackData);
          }
        },
        (error) => {
          // Handle listener errors
          clearTimeout(timeoutId);
          if (unsubscribe) {
            unsubscribe();
          }
          reject(error);
        }
      );
    });

    try {
      const ackData = await waitForAck;

      // Return the response data from the acknowledgement
      response.status(200).json({
        success: true,
        response: ackData.response,
        timestamp: ackData.timestamp,
      });
    } catch (error) {
      if (error instanceof Error && error.message.includes("Timeout")) {
        logger.warn(
          `Timeout ack of command ${commandId} from device ${deviceId}`
        );
        response.status(408).json({
          error: "Timeout waiting for device acknowledgement",
        });
      } else {
        throw error; // Re-throw other errors to be caught by outer try-catch
      }
    }
  } catch (error) {
    logger.error("Error sending command:", error);
    response.status(500).json({
      error: "Internal server error",
    });
  }
});
