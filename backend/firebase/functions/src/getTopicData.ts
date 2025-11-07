import {onRequest} from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import {getFirestore} from "firebase-admin/firestore";
import {
  TopicDataDocument,
  GetTopicDataRequest,
  GetTopicDataResponse,
} from "./types";

export const getTopicData = onRequest(async (request, response) => {
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

    // Extract request data from body
    const {deviceId, topicId, lastTimestamp}: GetTopicDataRequest =
      request.body;

    if (!deviceId || !topicId || lastTimestamp === undefined) {
      response.status(400).json({
        error:
          "Missing required parameters: deviceId, topicId, and lastTimestamp",
      });
      return;
    }

    logger.info(
      `Fetching data for: ${deviceId}, topic: ${topicId}`,
    );

    // Initialize Firestore
    const db = getFirestore();

    // Get the topic document reference
    const topicRef = db
      .collection("topics")
      .doc(deviceId)
      .collection("topics")
      .doc(topicId);

    // Check if topic exists
    const topicDoc = await topicRef.get();

    if (!topicDoc.exists) {
      logger.warn(
        `Topic not found for device: ${deviceId}, topic: ${topicId}`,
      );
      response.status(404).json({
        error: "Topic not found",
      });
      return;
    }

    const topicData = topicDoc.data() as TopicDataDocument;

    // Check if topic is inactive
    if (!topicData.active) {
      response.status(404).json({
        error: "Topic is inactive",
      });
      return;
    }

    // Check if current data is newer than lastTimestamp
    if (topicData.timestamp > lastTimestamp) {
      logger.info(
        `Topic data is newer for device: ${deviceId}, topic: ${topicId}`,
      );
      const responseData: GetTopicDataResponse = {
        data: topicData.data,
        timestamp: topicData.timestamp,
      };
      response.status(200).json(responseData);
      return;
    }

    // Data is not newer, set up listener to wait for new data
    logger.info(
      `Waiting for new topic data for device: ${deviceId}, topic: ${topicId}`,
    );

    // Create a promise that resolves when new data arrives or timeout occurs
    const waitForUpdate = new Promise<TopicDataDocument>((resolve, reject) => {
      let listenerUnsubscribed = false;
      let isFirstSnapshot = true;
      const initialTimestamp = topicData.timestamp;
      let listener: (() => void) | null = null;

      // Set up timeout (60 seconds)
      const timeoutId = setTimeout(() => {
        cleanup();
        reject(new Error("Topic data timeout"));
      }, 60000);

      // Cleanup function
      const cleanup = () => {
        if (!listenerUnsubscribed) {
          listenerUnsubscribed = true;
          if (timeoutId) {
            clearTimeout(timeoutId);
          }
          if (listener) {
            listener();
          }
        }
      };

      // Handle client disconnection
      response.on("close", () => {
        cleanup();
      });

      // Set up document listener
      listener = topicRef.onSnapshot(
        (snapshot) => {
          if (!snapshot.exists) {
            return;
          }

          const updatedData = snapshot.data() as TopicDataDocument;

          // Skip the initial snapshot (we already checked it)
          if (isFirstSnapshot) {
            isFirstSnapshot = false;
            // Only skip if it's the same document we already read
            // If it was updated between our read and listener setup, process it
            if (
              updatedData.timestamp === initialTimestamp
            ) {
              return;
            }
          }

          // Check if topic became inactive
          if (!updatedData.active) {
            if (!listenerUnsubscribed) {
              cleanup();
              resolve(updatedData);
            }
            return;
          }

          // Check if timestamp is newer
          if (updatedData.timestamp > lastTimestamp) {
            if (!listenerUnsubscribed) {
              cleanup();
              resolve(updatedData);
            }
          }
        },
        (error) => {
          if (!listenerUnsubscribed) {
            cleanup();
            reject(error);
          }
        },
      );
    });

    // Wait for update or timeout
    try {
      const updatedData = await waitForUpdate;

      // Check if client is still connected before sending response
      if (response.headersSent) {
        logger.warn("Response already sent, client may have disconnected");
        return;
      }

      const responseData: GetTopicDataResponse = {
        data: updatedData.data,
        timestamp: updatedData.timestamp,
      };

      response.status(200).json(responseData);
    } catch (error) {
      // Check if error is timeout

      if (error instanceof Error && error.message === "Topic data timeout") {
        logger.warn(
          `Timeout waiting for topic data: ${deviceId}, topic: ${topicId}`,
        );
        // Check if client is still connected
        if (!response.headersSent) {
          response.status(408).json({
            error: "Timeout waiting for topic data update",
          });
        }
      } else {
        logger.error("Error waiting for topic data update:", error);
        if (!response.headersSent) {
          response.status(500).json({
            error: "Internal server error",
          });
        }
      }
    }
  } catch (error) {
    logger.error("Error fetching topic data:", error);
    if (!response.headersSent) {
      response.status(500).json({
        error: "Internal server error",
      });
    }
  }
});
