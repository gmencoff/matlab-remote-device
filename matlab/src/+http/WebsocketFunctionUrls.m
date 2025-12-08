classdef WebsocketFunctionUrls < http.FunctionUrls
    % URLs for the firebase functions

     properties (Constant)
         SendCommand = 'https://remote-gateway-ts-tgyovhjiqq-uk.a.run.app/sendCommand';
         GetConfig = 'https://remote-gateway-ts-tgyovhjiqq-uk.a.run.app/getConfig';
         GetTopicData = 'NA';
     end
end