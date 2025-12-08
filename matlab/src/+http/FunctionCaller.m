classdef FunctionCaller < handle

    % Call API functions for getting config and sending commands

    methods (Abstract)
        ack = sendCommand(obj,cmd,timeout)    
        pollConfig(obj)
        topicData = getTopicData(obj, topicId, lastTimestamp)
        setConfigCallback(obj,callback)
    end
end