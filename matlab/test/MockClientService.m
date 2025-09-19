classdef MockClientService < client.ClientService
    %MOCKCLIENTSERVICE Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        ResponseToSend
        SentCommands = {}
        Callback
    end
    
    methods
        function response = sendCommand(obj, cmd, ~)
        % Send a command and block until ack is received
        % Args:
        %   cmd - struct containing command data
        %   timeout - timeout in seconds (default 5.0)
        % Returns:
        %   response - struct containing acknowledgment data
        obj.SentCommands{end+1} = cmd;
        response = obj.ResponseToSend;
        end
        
        function subscribeConfig(obj, callback)
        % Register a callback for config changes
        % Args:
        %   callback - function handle that accepts config struct
            obj.Callback = callback;
        end

        function updateConfig(obj,config)
            obj.Callback(config);
        end
    end
end

