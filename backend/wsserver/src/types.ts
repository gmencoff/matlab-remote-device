/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * TypeScript interfaces for Firestore document types
 */

// Configuration document structure
export interface ConfigDocument {
    id: string;
    config: any; // The actual configuration data from the caller
    timestamp: number;
    lastUpdated: number;
  }
  
  // Command document structure
  export interface CommandDocument {
    deviceId: string;
    commandId: string;
    command: any; // The actual command payload from the caller
    timestamp: number;
    answered: boolean; // Whether this command has been acknowledged
  }
  
  // Acknowledgement document structure
  export interface AckDocument {
    deviceId: string;
    commandId: string;
    response: any; // The response payload from the device
    timestamp: number;
  }
  
  // Request/Response interfaces for the REST functions
  
  // setConfig request
  export interface SetConfigRequest {
    deviceId: string;
    config: any; // The configuration data to store
  }
  
  // getCommand response
  export interface GetCommandResponse {
    command: CommandDocument | null;
  }
  
  // sendAck request
  export interface SendAckRequest {
    deviceId: string;
    commandId: string;
    response: any; // The response data from the device
  }
  
  export interface CommandRequest {
    deviceId: string;
    commandId: string;
    command: any; // The actual command payload
  }
  
  // Topic data document structure
  export interface TopicDataDocument {
    data: any; // The actual topic data from the caller
    timestamp: number;
    active: boolean; // Whether this topic is active
  }
  
  // setTopicData request
  export interface SetTopicDataRequest {
    deviceId: string;
    topicId: string;
    data: any; // The topic data to store
  }
  
  // getTopicData request
  export interface GetTopicDataRequest {
    deviceId: string;
    topicId: string;
    lastTimestamp: number; // Timestamp of the last data message received
  }
  
  // getTopicData response
  export interface GetTopicDataResponse {
    data: any; // The topic data
    timestamp: number;
  }
  
  // activateTopic request
  export interface ActivateTopicRequest {
    deviceId: string;
    topicId: string;
    active: boolean; // Whether to activate or deactivate the topic
  }
  