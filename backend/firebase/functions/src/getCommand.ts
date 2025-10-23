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

    logger.info(`Listening for unanswered commands for device: ${deviceId}`);

    // Initialize Firestore
    const db = getFirestore();

    // Set up real-time listener for unanswered commands
    const unsubscribe = db
      .collection("commands")
      .doc(deviceId)
      .collection("commands")
      .where("answered", "==", false)
      .orderBy("timestamp", "asc")
      .limit(1) // Only get the oldest command
      .onSnapshot(
        (snapshot) => {
          if (snapshot.empty) {
            logger.info(`No unanswered commands found for device: ${deviceId}`);
            // Don't send response yet, keep listening
            return;
          }

          // Get the oldest command
          const oldestCommandDoc = snapshot.docs[0];
          const commandData = oldestCommandDoc.data() as CommandDocument;

          logger.info(
            `Found oldest unanswered command for device: ${deviceId}, ` +
            `commandId: ${commandData.commandId}`
          );

          const responseData: GetCommandResponse = {
            command: commandData,
          };

          // Send the response and clean up
          response.status(200).json(responseData);
          unsubscribe(); // Stop listening after sending the command
        },
        (error) => {
          logger.error("Error listening for commands:", error);
          response.status(500).json({
            error: "Internal server error",
          });
          unsubscribe(); // Clean up on error
        }
      );

    // Set up timeout to prevent hanging connections
    const timeout = setTimeout(() => {
      logger.warn(
        `Timeout reached for device: ${deviceId}, no command available`
      );
      response.status(204).json({
        command: null,
      });
      unsubscribe();
    }, 300000); // 300 second timeout

    // Clean up timeout when response is sent
    response.on("close", () => {
      clearTimeout(timeout);
      unsubscribe();
    });
  } catch (error) {
    logger.error("Error setting up command listener:", error);
    response.status(500).json({
      error: "Internal server error",
    });
  }
});
