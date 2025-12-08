classdef (Abstract) FunctionUrls
    % Hold function URLs

    properties (Abstract, Constant)
        SendCommand
        GetConfig
        GetTopicData
    end

end