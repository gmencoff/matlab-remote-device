import {onRequest} from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import {getFirestore} from "firebase-admin/firestore";

export const getConfig = onRequest(async (request, response) => {
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
    // Only allow GET requests
    if (request.method !== "GET") {
      response.status(405).json({
        error: "Method not allowed. Only GET requests are supported.",
      });
      return;
    }

    // Extract config ID from query parameters
    const deviceId = request.query.id as string;

    if (!deviceId) {
      response.status(400).json({
        error: "Missing required parameter: id",
      });
      return;
    }

    logger.info(`Fetching config with ID: ${deviceId}`);

    // Initialize Firestore
    const db = getFirestore();

    // Get the config document from the 'devices' collection
    const configDoc = await db.collection("devices").doc(deviceId).get();

    if (!configDoc.exists) {
      logger.warn(`Config not found with ID: ${deviceId}`);
      response.status(404).json({
        error: "Config not found",
      });
      return;
    }

    // Return the config data
    const configData = configDoc.data();
    logger.info(`Successfully retrieved config: ${deviceId}`);

    response.status(200).json({
      id: deviceId,
      data: configData,
    });
  } catch (error) {
    logger.error("Error fetching config:", error);
    response.status(500).json({
      error: "Internal server error",
    });
  }
});
