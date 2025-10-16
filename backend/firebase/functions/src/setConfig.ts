import {onRequest} from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import {getFirestore} from "firebase-admin/firestore";
import {ConfigDocument, SetConfigRequest} from "./types";

export const setConfig = onRequest(async (request, response) => {
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

    // Extract config data from request body
    const {deviceId, config}: SetConfigRequest = request.body;

    if (!deviceId || !config) {
      response.status(400).json({
        error: "Missing required parameters: deviceId and config",
      });
      return;
    }

    logger.info(`Setting config for device: ${deviceId}`);

    // Initialize Firestore
    const db = getFirestore();

    // Create the config document
    const configDocument: ConfigDocument = {
      id: deviceId,
      data: config,
      timestamp: Date.now(),
      lastUpdated: Date.now(),
    };

    // Write config to Firestore in the devices collection
    await db.collection("devices").doc(deviceId).set(configDocument);

    logger.info(`Config successfully set for device: ${deviceId}`);

    response.status(200).json({
      success: true,
      message: "Config successfully set",
      deviceId: deviceId,
      timestamp: configDocument.timestamp,
    });
  } catch (error) {
    logger.error("Error setting config:", error);
    response.status(500).json({
      error: "Internal server error",
    });
  }
});
