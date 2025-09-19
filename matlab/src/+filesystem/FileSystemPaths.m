classdef FileSystemPaths < handle
    % Shared configuration for file paths used by both client and edge services
    
    properties (SetAccess = private)
        root
        configDir
        commandsDir
        acksDir
        configPath
        commandsPath
    end
    
    methods
        function obj = FileSystemPaths(root)
            obj.root = root;
            obj.configDir = fullfile(root, 'config');
            obj.commandsDir = fullfile(root, 'commands');
            obj.acksDir = fullfile(obj.commandsDir, 'acks');
            
            % Ensure directories exist
            if ~exist(obj.configDir, 'dir')
                mkdir(obj.configDir);
            end
            if ~exist(obj.commandsDir, 'dir')
                mkdir(obj.commandsDir);
            end
            if ~exist(obj.acksDir, 'dir')
                mkdir(obj.acksDir);
            end
            
            % Define file paths
            obj.configPath = fullfile(obj.configDir, 'config.json');
            obj.commandsPath = fullfile(obj.commandsDir, 'commands.jsonl');
        end
        
        function ackPath = getAckPath(obj, commandId)
            % Get the path for a specific command acknowledgment file
            ackPath = fullfile(obj.acksDir, [char(string(commandId)) '.json']);
        end
    end
end
