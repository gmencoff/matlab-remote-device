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
