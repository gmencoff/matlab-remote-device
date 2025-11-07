import {onRequest} from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import {getFirestore} from "firebase-admin/firestore";
import {TopicDataDocument, ActivateTopicRequest} from "./types";

export const activateTopic = onRequest(async (request, response) => {
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

    // Extract activation data from request body
    const {deviceId, topicId, active}: ActivateTopicRequest = request.body;

    if (!deviceId || !topicId || active === undefined) {
      response.status(400).json({
        error: "Missing required parameters: deviceId, topicId, and active",
      });
      return;
    }

    logger.info(
      `Setting topic status to ${active} for: ${deviceId}, topic: ${topicId}`,
    );

    // Initialize Firestore
    const db = getFirestore();

    // Get topic document reference
    const topicRef = db
      .collection("topics")
      .doc(deviceId)
      .collection("topics")
      .doc(topicId);

    // Get existing document to preserve data if it exists
    const existingDoc = await topicRef.get();
    const existingData = existingDoc.exists ?
      (existingDoc.data() as TopicDataDocument).data :
      null;

    // Create the topic document with active status
    const topicDocument: TopicDataDocument = {
      data: existingData,
      timestamp: Date.now(),
      active: active,
    };

    // Write topic document to Firestore
    await topicRef.set(topicDocument);

    logger.info(
      `Topic status set for device: ${deviceId}, topic: ${topicId}`,
    );

    response.status(200).json({
      success: true,
      message: "Topic active status successfully set",
      deviceId: deviceId,
      topicId: topicId,
      active: active,
      timestamp: topicDocument.timestamp,
    });
  } catch (error) {
    logger.error("Error setting topic active status:", error);
    response.status(500).json({
      error: "Internal server error",
    });
  }
});

