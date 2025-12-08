classdef EmptyFunctionCaller < http.FunctionCaller

    % No op function caller
    
    methods
        function ack = sendCommand(~,~,~)    
            ack = [];
        end

        function pollConfig(~)

        end

        function topicData = getTopicData(~, ~, ~)
            topicData = [];
        end

        function setConfigCallback(~,~)

        end
    end
end