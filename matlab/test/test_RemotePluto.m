classdef test_RemotePluto < matlab.unittest.TestCase
    % Test RemotePluto set and get methods
    
    properties
        mockClientService
        remotePluto
    end
    
    methods (TestMethodSetup)
        function setup(testCase)
            % Create mock client service
            testCase.mockClientService = MockClientService();
            testCase.remotePluto = pluto.RemotePluto(testCase.mockClientService);
        end
    end
    
    methods (Test)
        function test_get_existing_property(testCase)
            % Test getting an existing property
            testConfig = struct('frequency', 2.4e9, 'gain', 30, 'sample_rate', 1e6);
            
            % Simulate config update
            testCase.triggerConfigUpdate(testConfig);
            
            % Test getting properties
            testCase.verifyEqual(testCase.remotePluto.get('frequency'), 2.4e9);
            testCase.verifyEqual(testCase.remotePluto.get('gain'), 30);
            testCase.verifyEqual(testCase.remotePluto.get('sample_rate'), 1e6);
        end
        
        function test_get_nonexistent_property(testCase)
            % Test getting a non-existent property
            testConfig = struct('frequency', 2.4e9);
            testCase.triggerConfigUpdate(testConfig);
            testCase.verifyError(@() testCase.remotePluto.get('nonexistent'),?MException);
        end
        
        function test_set_property_success(testCase)
            % Test successful property setting
            newFreq = 5.8e9;
            
            % Mock successful response
            ack = commands.PropertyAck('test-id',true,newFreq,'');
            testCase.mockClientService.ResponseToSend = ack;
            
            % Set property
            testCase.remotePluto.set('frequency', newFreq);
            
            % Verify command was sent
            testCase.verifyNumElements(testCase.mockClientService.SentCommands,1);
            cmd = testCase.mockClientService.SentCommands{1};
            testCase.verifyEqual(cmd.name, 'frequency');
            testCase.verifyEqual(cmd.value, newFreq);
            testCase.verifyEqual(cmd.type, 'property');
            
            % Verify internal state was updated
            testCase.verifyEqual(testCase.remotePluto.get('frequency'), newFreq);
        end
        
        function test_set_property_failure(testCase)
            % Test property setting failure
            % Mock failure response
            ack = commands.PropertyAck('test-id',false,0,'error');
            testCase.mockClientService.ResponseToSend = ack;
            
            % Verify error is thrown
            testCase.verifyError(@() testCase.remotePluto.set('frequency', -1),?MException);
        end
        
        function test_callMethod_success(testCase)
            % Test successful method call
            expectedResult = 1;
            
            % Mock successful response
            ack = commands.MethodAck('test-id',true,1,'');
            testCase.mockClientService.ResponseToSend = ack;
            
            % Call method
            result = testCase.remotePluto.callMethod('start');

            % Verify command was sent
            testCase.verifyNumElements(testCase.mockClientService.SentCommands,1);
            cmd = testCase.mockClientService.SentCommands{1};
            testCase.verifyEqual(cmd.name, 'start');
            testCase.verifyEqual(cmd.type, 'method');
            
            % Verify result
            testCase.verifyEqual(result, expectedResult);
        end
                
        function test_getPropertyNames(testCase)
            % Test getting property names
            testConfig = struct('frequency', 2.4e9, 'gain', 30, 'sample_rate', 1e6);
            testCase.triggerConfigUpdate(testConfig);
            
            names = testCase.remotePluto.getPropertyNames();
            expectedNames = {'frequency'; 'gain'; 'sample_rate'};
            
            testCase.verifyEqual(sort(names), sort(expectedNames));
        end
        
        function test_config_updates(testCase)
            % Test that config updates are properly handled
            % Initial config
            config1 = struct('frequency', 2.4e9, 'gain', 30);
            testCase.triggerConfigUpdate(config1);
            
            testCase.verifyEqual(testCase.remotePluto.get('frequency'), 2.4e9);
            testCase.verifyEqual(testCase.remotePluto.get('gain'), 30);
            
            % Updated config
            config2 = struct('frequency', 5.8e9, 'gain', 20, 'sample_rate', 2e6);
            testCase.triggerConfigUpdate(config2);
            
            testCase.verifyEqual(testCase.remotePluto.get('frequency'), 5.8e9);
            testCase.verifyEqual(testCase.remotePluto.get('gain'), 20);
            testCase.verifyEqual(testCase.remotePluto.get('sample_rate'), 2e6);
        end
    end
    
    methods (Access = private)
        function mockService = createMockClientService(testCase)
            % Create a mock client service
            mockService = struct();
            mockService.nextResponse = struct();
            
            mockService.sendCommand = @(cmd, timeout) testCase.mockSendCommand(cmd, timeout);
            mockService.subscribeConfig = @(callback) testCase.mockSubscribeConfig(callback);
        end
        
        function response = mockSendCommand(testCase, cmd, ~)
            % Mock sendCommand implementation
            testCase.sentCommands{end+1} = cmd;
            response = testCase.mockClientService.nextResponse;
        end
        
        function mockSubscribeConfig(testCase, callback)
            % Mock subscribeConfig implementation
            testCase.configCallbacks{end+1} = callback;
        end

        function triggerConfigUpdate(testCase,config)
            testCase.mockClientService.updateConfig(config);
        end
    end
end
