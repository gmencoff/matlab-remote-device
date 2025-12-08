classdef HttpClientService < client.ClientService
    properties (Access = private)
        FunctionCaller (1,1) http.FunctionCaller = http.EmptyFunctionCaller
        PollInterval
        ConfigTimer
    end

    methods
        function obj = HttpClientService(deviceId,optargs)
            arguments
                deviceId
                optargs.PollInterval = 10
            end
            
            obj.FunctionCaller = http.FirebaseFunctionCaller(deviceId);
            obj.PollInterval = optargs.PollInterval;
        end
        
        function response = sendCommand(obj, cmd, timeout)
            response = obj.FunctionCaller.sendCommand(cmd,timeout);
        end
        
        function subscribeConfig(obj, callback)
            % Poll config.json and invoke callback whenever it changes
            obj.FunctionCaller.setConfigCallback(callback);
            
            % Start polling timer
            fcnCaller = obj.FunctionCaller;
            obj.ConfigTimer = timer('ExecutionMode', 'fixedRate', ...
                                  'Period', obj.PollInterval, ...
                                  'TimerFcn', @(~,~)pollConfig(fcnCaller));
            start(obj.ConfigTimer);
        end
        
        function topicData = getTopicData(obj, topicId, lastTimestamp)
            topicData = obj.FunctionCaller.getTopicData(topicId, lastTimestamp);
        end

        function delete(obj)
            if ~isempty(obj.ConfigTimer)
                stop(obj.ConfigTimer);
            end
        end
    end
end