classdef test_Pluto_Fs_Integration < matlab.unittest.TestCase
    % Integration test for the complete client-side system
    
    properties
        testDir
        clientService
        remotePluto
        paths
    end
    
    methods (TestMethodSetup)
        function setup(testCase)
            % Create temporary directory and full system
            testCase.testDir = fullfile(tempdir, ['integration_test_' char(java.util.UUID.randomUUID())]);
            testCase.clientService = filesystem.FileSystemClientService(testCase.testDir, 0.1);
            testCase.remotePluto = pluto.RemotePluto(testCase.clientService);
            testCase.paths = filesystem.FileSystemPaths(testCase.testDir);
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
        function test_end_to_end_property_operations(testCase)
            % Test complete property get/set workflow

            import matlab.unittest.constraints.Eventually
            import matlab.unittest.constraints.IsEqualTo
            
            % 1. Set up initial config
            initialConfig = struct('frequency', 2.4e9, 'gain', 30, 'sample_rate', 1e6);
            testCase.writeJson(testCase.paths.configPath, initialConfig);
            
            % 2. Verify initial properties can be read
            testCase.verifyThat(@()testCase.getPropertyWithError('frequency'),Eventually(IsEqualTo(2.4e9)));
            testCase.verifyThat(@()testCase.getPropertyWithError('gain'),Eventually(IsEqualTo(30)));
            
            % 3. Test property setting with mock edge response
            newFreq = 5.8e9;
            
            % Set property (this will block until ack is received)
            testCase.setPropertyWithResponse('frequency',newFreq);
            
            % 4. Verify property was updated locally
            testCase.verifyEqual(testCase.remotePluto.get('frequency'), newFreq);
            
            % 5. Verify command was written to commands file
            testCase.verifyTrue(exist(testCase.paths.commandsPath, 'file') == 2);
            
            % Read and verify command
            commands = testCase.readCommandsFile();
            testCase.verifyNumElements(commands, 1);
            testCase.verifyEqual(commands{1}.type, 'property');
            testCase.verifyEqual(commands{1}.name, 'frequency');
            testCase.verifyEqual(commands{1}.value, newFreq);
        end
        
        function test_end_to_end_method_operations(testCase)
            % Test complete method call workflow
            
            methodName = 'calibrate';
            expectedResult = struct('status', 'success', 'calibration_data', [1;2;3;4]);
            
            % Start background task to simulate edge processing
            result = callMethodWithResponse(testCase,methodName,expectedResult);
            
            % Verify result
            testCase.verifyEqual(result.status, expectedResult.status);
            testCase.verifyEqual(result.calibration_data, expectedResult.calibration_data);
            
            % Verify command was written
            commands = testCase.readCommandsFile();
            testCase.verifyNumElements(commands, 1);
            testCase.verifyEqual(commands{1}.type, 'method');
            testCase.verifyEqual(commands{1}.name, methodName);
        end
        
        function test_config_synchronization(testCase)
            % Test that config changes are properly synchronized
            
            % Initial config
            config1 = struct('frequency', 2.4e9, 'gain', 30);
            testCase.writeJson(testCase.paths.configPath, config1);
            pause(0.2);
            
            testCase.verifyEqual(testCase.remotePluto.get('frequency'), 2.4e9);
            testCase.verifyEqual(testCase.remotePluto.get('gain'), 30);
            
            % Update config (simulating edge updating the config)
            config2 = struct('frequency', 5.8e9, 'gain', 20, 'sample_rate', 2e6);
            testCase.writeJson(testCase.paths.configPath, config2);
            pause(0.2);
            
            % Verify changes are reflected
            testCase.verifyEqual(testCase.remotePluto.get('frequency'), 5.8e9);
            testCase.verifyEqual(testCase.remotePluto.get('gain'), 20);
            testCase.verifyEqual(testCase.remotePluto.get('sample_rate'), 2e6);
            
            % Verify property names are updated
            names = testCase.remotePluto.getPropertyNames();
            testCase.verifyTrue(ismember('sample_rate', names));
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
        
        function commands = readCommandsFile(testCase)
            % Read and parse commands from the commands.jsonl file
            commands = {};
            if ~exist(testCase.paths.commandsPath, 'file')
                return;
            end
            
            fid = fopen(testCase.paths.commandsPath, 'r');
            if fid == -1
                return;
            end
            
            try
                lineNum = 1;
                while ~feof(fid)
                    line = fgetl(fid);
                    if ischar(line) && ~isempty(strtrim(line))
                        commands{lineNum} = jsondecode(line); %#ok<AGROW>
                        lineNum = lineNum + 1;
                    end
                end
                fclose(fid);
            catch ME
                fclose(fid);
                rethrow(ME);
            end
        end

        function setPropertyWithResponse(testCase, name, value)
            % Start background task to simulate edge processing
            t = timer('ExecutionMode','fixedRate','TimerFcn',@(~,~) testCase.simulateEdgePropertyResponse(value));
            start(t);

            testCase.remotePluto.set(name,value);
        end

        function actresult = callMethodWithResponse(testCase,method,result)
            % Start background task to simulate edge processing
            t = timer('ExecutionMode','fixedRate','TimerFcn', @(~,~)testCase.simulateEdgeMethodResponse(result));
            start(t);
            
            % Call method
            actresult = testCase.remotePluto.callMethod(method);
        end
        
        function simulateEdgePropertyResponse(testCase, value)
            % Simulate edge processing a property command
            commands = testCase.readCommandsFile();
            if isempty(commands)
                return;
            end
            
            % Get the latest command
            latestCommand = commands{end};
            
            % Create acknowledgment
            ackData = struct('id', latestCommand.id, 'ok', true, 'type', 'property', ...
                           'value', value, 'ts', posixtime(datetime('now')));
            
            % Write acknowledgment file
            ackPath = testCase.paths.getAckPath(latestCommand.id);
            testCase.writeJson(ackPath, ackData);
        end
        
        function simulateEdgeMethodResponse(testCase, result)
            % Simulate edge processing a method command
            commands = testCase.readCommandsFile();
            if isempty(commands)
                return;
            end
            
            % Get the latest command
            latestCommand = commands{end};
            
            % Create acknowledgment
            ackData = struct('id', latestCommand.id, 'ok', true, 'type', 'method', ...
                           'result', result, 'ts', posixtime(datetime('now')));
            
            % Write acknowledgment file
            ackPath = testCase.paths.getAckPath(latestCommand.id);
            testCase.writeJson(ackPath, ackData);
        end
        
        function simulateMultipleEdgeResponses(testCase)
            % Simulate edge processing multiple commands
            commands = testCase.readCommandsFile();
            
            for i = 1:length(commands)
                cmd = commands{i};
                
                if strcmp(cmd.type, 'property')
                    ackData = struct('id', cmd.id, 'ok', true, 'type', 'property', ...
                                   'value', cmd.value, 'ts', posixtime(datetime('now')));
                elseif strcmp(cmd.type, 'method')
                    result = 'started';  % Mock result
                    ackData = struct('id', cmd.id, 'ok', true, 'type', 'method', ...
                                   'result', result, 'ts', posixtime(datetime('now')));
                end
                
                ackPath = testCase.paths.getAckPath(cmd.id);
                testCase.writeJson(ackPath, ackData);
                
                % Small delay between responses
                pause(0.05);
            end
        end
        
        function simulateEdgeErrorResponse(testCase, commandType)
            % Simulate edge returning an error response
            commands = testCase.readCommandsFile();
            if isempty(commands)
                return;
            end
            
            % Get the latest command
            latestCommand = commands{end};
            
            % Create error acknowledgment
            ackData = struct('id', latestCommand.id, 'ok', false, 'type', commandType, ...
                           'error', 'Simulated edge error', 'ts', posixtime(datetime('now')));
            
            % Write acknowledgment file
            ackPath = testCase.paths.getAckPath(latestCommand.id);
            testCase.writeJson(ackPath, ackData);
        end

        function val = getPropertyWithError(testCase,name)
            try
                val = testCase.remotePluto.get(name);
            catch
                val = -1;
            end
        end
    end
end
