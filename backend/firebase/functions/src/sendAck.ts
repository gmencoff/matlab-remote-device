import {onRequest} from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import {getFirestore} from "firebase-admin/firestore";
import {AckDocument, SendAckRequest} from "./types";

export const sendAck = onRequest(async (request, response) => {
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

    // Extract ack data from request body
    // eslint-disable-next-line max-len
    const {deviceId, commandId, response: responseData}: SendAckRequest = request.body;

    if (!deviceId || !commandId || responseData === undefined) {
      response.status(400).json({
        error: "Missing required parameters: deviceId, commandId, and response",
      });
      return;
    }

    logger.info(`Sending ack for command ${commandId} from device ${deviceId}`);

    // Initialize Firestore
    const db = getFirestore();

    // Create the ack document
    const ackDocument: AckDocument = {
      deviceId,
      commandId,
      response: responseData,
      timestamp: Date.now(),
    };

    // Write ack to Firestore in the acks collection
    await db
      .collection("acks")
      .doc(deviceId)
      .collection("acks")
      .doc(commandId)
      .set(ackDocument);

    // Mark the corresponding command as answered
    await db
      .collection("commands")
      .doc(deviceId)
      .collection("commands")
      .doc(commandId)
      .update({answered: true});

    logger.info(`Ack sent for command ${commandId} from device ${deviceId}`);

    response.status(200).json({
      success: true,
      message: "Acknowledgement successfully sent",
      deviceId: deviceId,
      commandId: commandId,
      timestamp: ackDocument.timestamp,
    });
  } catch (error) {
    logger.error("Error sending ack:", error);
    response.status(500).json({
      error: "Internal server error",
    });
  }
});
