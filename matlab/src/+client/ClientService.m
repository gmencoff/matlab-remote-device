classdef (Abstract) ClientService < handle
    % Abstract base class for client services
    
    methods (Abstract)
        response = sendCommand(obj, cmd, timeout)
        % Send a command and block until ack is received
        % Args:
        %   cmd - struct containing command data
        %   timeout - timeout in seconds (default 5.0)
        % Returns:
        %   response - struct containing acknowledgment data
        
        subscribeConfig(obj, callback)
        % Register a callback for config changes
        % Args:
        %   callback - function handle that accepts config struct
    end
end
