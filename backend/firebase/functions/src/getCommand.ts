import {onRequest} from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import {getFirestore} from "firebase-admin/firestore";
import {CommandDocument, GetCommandResponse} from "./types";

export const getCommand = onRequest(async (request, response) => {
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

    // Extract device ID from query parameters
    const deviceId = request.query.deviceId as string;

    if (!deviceId) {
      response.status(400).json({
        error: "Missing required parameter: deviceId",
      });
      return;
    }

    logger.info(`Fetching unanswered commands for device: ${deviceId}`);

    // Initialize Firestore
    const db = getFirestore();

    // Get all commands for the device that haven't been answered
    const commandsQuery = await db
      .collection("commands")
      .doc(deviceId)
      .collection("commands")
      .where("answered", "==", false)
      .orderBy("timestamp", "asc")
      .get();

    const commands: CommandDocument[] = [];
    commandsQuery.forEach((doc) => {
      const commandData = doc.data() as CommandDocument;
      commands.push(commandData);
    });

    logger.info(`Found ${commands.length} unanswered for: ${deviceId}`);

    const responseData: GetCommandResponse = {
      commands: commands,
    };

    response.status(200).json(responseData);
  } catch (error) {
    logger.error("Error fetching commands:", error);
    response.status(500).json({
      error: "Internal server error",
    });
  }
});
