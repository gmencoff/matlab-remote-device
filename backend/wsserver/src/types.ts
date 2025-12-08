/* eslint-disable @typescript-eslint/no-explicit-any */
  
  // Request/Response interfaces for the REST and WS server functions
 
    export interface DeviceHelloMessage {
        type: "hello";
        deviceId: string;
        config: any;
    }

    export interface DeviceCommandAckMessage {
        type: "ack";
        deviceId: string;
        commandId: string;
        status: "ok" | "error";
        response: any;
    }

    export interface DeviceSetConfigMessage {
        type: "setConfig";
        deviceId: string;
        config: any;
    }

    export type IncomingDeviceMessage = DeviceHelloMessage | DeviceCommandAckMessage | DeviceSetConfigMessage;

   // getConfig request
   export interface GetConfigRequest {
    deviceId: string;
  }
  
  // setConfig request
  export interface SetConfigRequest {
    deviceId: string;
    config: any; // The configuration data to store
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
  