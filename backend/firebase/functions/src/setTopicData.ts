import {onRequest} from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import {getFirestore} from "firebase-admin/firestore";
import {TopicDataDocument, SetTopicDataRequest} from "./types";

export const setTopicData = onRequest(async (request, response) => {
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

    // Extract topic data from request body
    const {deviceId, topicId, data}: SetTopicDataRequest =
      request.body;

    if (!deviceId || !topicId || data === undefined) {
      response.status(400).json({
        error: "Missing required parameters: deviceId, topicId, and data",
      });
      return;
    }

    logger.info(`Setting topic data for: ${deviceId}, topic: ${topicId}`);

    // Initialize Firestore
    const db = getFirestore();

    // Get existing topic document to check if it's active
    const topicRef = db
      .collection("topics")
      .doc(deviceId)
      .collection("topics")
      .doc(topicId);
    const existingDoc = await topicRef.get();

    // Check if topic exists
    if (!existingDoc.exists) {
      logger.warn(
        `Topic not found for device: ${deviceId}, topic: ${topicId}`,
      );
      response.status(404).json({
        error: "Topic not found. Use activateTopic to create the topic first.",
      });
      return;
    }

    const existingTopicData = existingDoc.data() as TopicDataDocument;

    // Check if topic is active
    if (!existingTopicData.active) {
      logger.warn(
        `Topic is inactive for device: ${deviceId}, topic: ${topicId}`,
      );
      response.status(400).json({
        error: "Topic is inactive. Use activateTopic to activate it first.",
      });
      return;
    }

    // Create the topic data document, preserving active status
    const topicDocument: TopicDataDocument = {
      data: data,
      timestamp: Date.now(),
      active: existingTopicData.active,
    };

    // Write topic data to Firestore, overwriting existing data
    await topicRef.set(topicDocument);

    logger.info(
      `Topic data successfully set for device: ${deviceId}, topic: ${topicId}`,
    );

    response.status(200).json({
      success: true,
      message: "Topic data successfully set",
      deviceId: deviceId,
      topicId: topicId,
      timestamp: topicDocument.timestamp,
      active: topicDocument.active,
    });
  } catch (error) {
    logger.error("Error setting topic data:", error);
    response.status(500).json({
      error: "Internal server error",
    });
  }
});
