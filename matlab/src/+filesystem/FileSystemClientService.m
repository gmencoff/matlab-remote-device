classdef FileSystemClientService < client.ClientService
    % File-system-based client service.
    % Uses JSON files under a root directory to sync config and send commands.
    % Intended for OneDrive/Dropbox/etc. synced folders.
    
    properties (Access = private)
        paths
        pollInterval
        configTimer
        lastConfig
        configCallback
    end
    
    methods
        function obj = FileSystemClientService(root, pollInterval)
            arguments
                root
                pollInterval = 1
            end

            obj.paths = filesystem.FileSystemPaths(root);
            obj.pollInterval = pollInterval;
        end
        
        function response = sendCommand(obj, cmd, timeout)
            % Append command to commands.jsonl, then wait for its ack
            arguments
                obj
                cmd
                timeout = 5
            end
            
            % Write command to file
            fid = fopen(obj.paths.commandsPath, 'a');
            if fid == -1
                error('Could not open commands file for writing');
            end
            try
                fprintf(fid, '%s\n', jsonencode(cmd));
                fclose(fid);
            catch ME
                fclose(fid);
                rethrow(ME);
            end
            
            % Wait for acknowledgment
            ackPath = obj.paths.getAckPath(cmd.id);

            t = tic;
            deadline = toc(t) + timeout;
            while toc(t) < deadline
                if exist(ackPath, 'file')
                    response = obj.readJson(ackPath);
                    return;
                end
                pause(0.1);
            end
            
            error('Timeout waiting for acknowledgment of command %s', cmd.id);
        end
        
        function subscribeConfig(obj, callback)
            % Poll config.json and invoke callback whenever it changes
            obj.configCallback = callback;
            
            % Emit initial config if available
            if exist(obj.paths.configPath, 'file')
                cfg = obj.readJson(obj.paths.configPath);
                obj.configCallback(cfg);
                obj.lastConfig = cfg;
            end
            
            % Start polling timer
            obj.configTimer = timer('ExecutionMode', 'fixedRate', ...
                                  'Period', obj.pollInterval, ...
                                  'TimerFcn', @(timer,evt)obj.pollConfig());
            start(obj.configTimer);
        end
        
        function delete(obj)
            % Cleanup timer on object destruction
            if ~isempty(obj.configTimer) && isvalid(obj.configTimer)
                stop(obj.configTimer);
                delete(obj.configTimer);
            end
        end
    end
    
    methods (Access = private)
        function pollConfig(obj)
            % Timer callback to poll for config changes
            if exist(obj.paths.configPath, 'file')
                try
                    cfg = obj.readJson(obj.paths.configPath);
                    if ~isequal(cfg, obj.lastConfig)
                        obj.configCallback(cfg);
                        obj.lastConfig = cfg;
                    end
                catch
                    % Ignore errors during polling
                end
            end
        end
        
        function data = readJson(~, filepath)
            % Read and parse JSON file
            fid = fopen(filepath, 'r');
            if fid == -1
                error('Could not open file: %s', filepath);
            end
            try
                raw = fread(fid, inf, 'char=>char')';
                fclose(fid);
                data = jsondecode(raw);
            catch ME
                fclose(fid);
                rethrow(ME);
            end
        end
    end
end
