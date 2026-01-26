classdef ApsClientService < client.ClientService
    properties (Access = private)
        DeviceId
        ConfigCallback
    end

    methods
        function obj = ApsClientService(deviceId)
            arguments
                deviceId
            end
            
            obj.DeviceId = deviceId;
        end
        
        function response = sendCommand(obj, cmd, timeout)
            % TODO: Implement the send command function
            response = []
        end
        
        function subscribeConfig(obj, callback)
            % TODO: Implement the subscribe config function
            obj.ConfigCallback = callback;
        end
        
        function topicData = getTopicData(obj, topicId, lastTimestamp)
            % TODO: Get topic data does not need to be implemented right
            % now
        end
    end
end