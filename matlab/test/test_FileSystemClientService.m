classdef test_FileSystemClientService < matlab.unittest.TestCase
    % Test FileSystemClientService functionality
    
    properties
        testDir
        clientService
        paths
        receivedConfigs
    end
    
    methods (TestMethodSetup)
        function setup(testCase)
            % Create temporary directory and client service
            testCase.testDir = fullfile(tempdir, ['test_' char(java.util.UUID.randomUUID())]);
            testCase.clientService = filesystem.FileSystemClientService(testCase.testDir, 0.1);
            testCase.paths = filesystem.FileSystemPaths(testCase.testDir);
            testCase.receivedConfigs = {};
        end
    end
    
    methods (TestMethodTeardown)
        function teardown(testCase)
            % Clean up
            delete(testCase.clientService);
            if exist(testCase.testDir, 'dir')
                rmdir(testCase.testDir, 's');
            end
        end
    end
    
    methods (Test)
        function test_sendPropertyCommand_success(testCase)
            % Test successful command sending and acknowledgment
            cmd = commands.PropertyCommand('Property',2.4e9);
            
            % Create mock acknowledgment file
            ackPath = testCase.paths.getAckPath(cmd.id);
            ack = commands.PropertyAck(cmd.id,true,cmd.value,'');
            ackData = ack.toDict();
            
            % Start async task to create ack file after delay
            t = timer('StartDelay', 1, 'TimerFcn', @(~,~) testCase.writeJson(ackPath, ackData), ...
                  'ExecutionMode', 'singleShot');
            start(t);
            
            % Send command and verify response
            response = testCase.clientService.sendCommand(cmd, 5);
            
            testCase.verifyEqual(response.id, cmd.id);
            testCase.verifyTrue(response.ok);
            testCase.verifyEqual(response.value, 2.4e9);
            
            % Verify command was written to file
            testCase.verifyTrue(exist(testCase.paths.commandsPath, 'file') == 2);
            
            % Read and verify command file content
            fid = fopen(testCase.paths.commandsPath, 'r');
            content = fread(fid, inf, 'char=>char')';
            fclose(fid);
            
            writtenCmd = jsondecode(strtrim(content));
            testCase.verifyEqual(writtenCmd.id, cmd.id);
            testCase.verifyEqual(writtenCmd.type, cmd.type);
        end

        function test_sendMethodCommand_success(testCase)
            % Test successful command sending and acknowledgment
            cmd = commands.MethodCommand('rx');
            
            % Create mock acknowledgment file
            ackPath = testCase.paths.getAckPath(cmd.id);
            ack = commands.MethodAck(cmd.id,true,[1;2;3],'');
            ackData = ack.toDict();
            
            % Start async task to create ack file after delay
            t = timer('StartDelay', 1, 'TimerFcn', @(~,~) testCase.writeJson(ackPath, ackData), ...
                  'ExecutionMode', 'singleShot');
            start(t);
            
            % Send command and verify response
            response = testCase.clientService.sendCommand(cmd, 5);
            
            testCase.verifyEqual(response.id, cmd.id);
            testCase.verifyTrue(response.ok);
            testCase.verifyEqual(response.result, [1;2;3]);
            
            % Verify command was written to file
            testCase.verifyTrue(exist(testCase.paths.commandsPath, 'file') == 2);
            
            % Read and verify command file content
            fid = fopen(testCase.paths.commandsPath, 'r');
            content = fread(fid, inf, 'char=>char')';
            fclose(fid);
            
            writtenCmd = jsondecode(strtrim(content));
            testCase.verifyEqual(writtenCmd.id, cmd.id);
            testCase.verifyEqual(writtenCmd.type, cmd.type);
        end
        
        function test_sendCommand_timeout(testCase)
            % Test command timeout
            cmd = commands.PropertyCommand('Property',2.4e9);
            
            % Don't create ack file - should timeout
            testCase.verifyError(@() testCase.clientService.sendCommand(cmd,1),?MException);
        end
        
        function test_subscribeConfig_initialConfig(testCase)
            % Test config subscription with initial config
            initialConfig = struct('frequency', 2.4e9, 'gain', 30, 'sample_rate', 1e6);
            
            % Write initial config
            testCase.writeJson(testCase.paths.configPath, initialConfig);
            
            % Set up callback to capture config updates
            callback = @(cfg) testCase.addReceivedConfig(cfg);
            
            % Subscribe to config changes
            testCase.clientService.subscribeConfig(callback);
            
            % Wait for initial config to be read
            pause(0.2);
            
            % Verify initial config was received
            testCase.verifyNumElements(testCase.receivedConfigs, 1);
            testCase.verifyEqual(testCase.receivedConfigs{1}.frequency, initialConfig.frequency);
            testCase.verifyEqual(testCase.receivedConfigs{1}.gain, initialConfig.gain);
            testCase.verifyEqual(testCase.receivedConfigs{1}.sample_rate, initialConfig.sample_rate);
        end
        
        function test_subscribeConfig_configChanges(testCase)

            import matlab.unittest.constraints.Eventually
            import matlab.unittest.constraints.IsEqualTo

            % Test config subscription with changes
            callback = @(cfg) testCase.addReceivedConfig(cfg);
            
            % Subscribe to config changes
            testCase.clientService.subscribeConfig(callback);
            
            % Write first config
            config1 = struct('frequency', 2.4e9);
            testCase.writeJson(testCase.paths.configPath, config1);

            % Verify first config
            testCase.verifyThat(@()length(testCase.receivedConfigs),Eventually(IsEqualTo(1)));
            testCase.verifyThat(@()testCase.receivedConfigs{1}.frequency,Eventually(IsEqualTo(config1.frequency)));           
            
            % Write second config
            config2 = struct('frequency', 5.8e9);
            testCase.writeJson(testCase.paths.configPath, config2);
            
            % Verify second config
            testCase.verifyThat(@()length(testCase.receivedConfigs),Eventually(IsEqualTo(2)));
            testCase.verifyThat(@()testCase.receivedConfigs{2}.frequency,Eventually(IsEqualTo(config2.frequency)));   
        end
        
        function test_multiple_commands(testCase)
            % Test sending multiple commands
            cmds = {
                commands.PropertyCommand('frequency',2.4e9),...
                commands.PropertyCommand('gain',30),...
                commands.MethodCommand('rx')
            };
            
            % Create ack files for all commands
            for i = 1:length(cmds)
                cmd = cmds{i};
                ackPath = testCase.paths.getAckPath(cmd.id);
                
                if strcmp(cmd.type, 'property')
                    ack = commands.PropertyAck(cmd.id,true,cmd.value,'');
                else
                    ack = commands.MethodAck(cmd.id,true,1,'');
                end
                ackData = ack.toDict();
                
                % Create ack file with delay
                t = timer('StartDelay', 0.1 * i, 'TimerFcn', @(~,~) testCase.writeJson(ackPath, ackData), ...
                      'ExecutionMode', 'singleShot');
                t.start();
            end
            
            % Send all commands
            responses = cell(size(cmds));
            for i = 1:length(cmds)
                responses{i} = testCase.clientService.sendCommand(cmds{i}, 2);
            end
            
            % Verify all responses
            for i = 1:length(responses)
                testCase.verifyEqual(responses{i}.id, cmds{i}.id);
                testCase.verifyTrue(responses{i}.ok);
            end
        end
    end
    
    methods (Access = private)
        function writeJson(~, filepath, data)
            % Helper method to write JSON data to file
            fid = fopen(filepath, 'w');
            if fid == -1
                error('Could not open file for writing: %s', filepath);
            end
            try
                fprintf(fid, '%s', jsonencode(data));
                fclose(fid);
            catch ME
                fclose(fid);
                rethrow(ME);
            end
        end

        function addReceivedConfig(testCase,cfg)
            testCase.receivedConfigs{end+1} = cfg;
        end
    end
end
