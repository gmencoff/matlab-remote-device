% Clear
clear;
close all;

%% Create remote pluto

id = 'gzVblueyGz';
sdr = pluto.RemotePluto(id);

%% Sequential Receive

fs = get(sdr,'sample_rate');
sa = spectrumAnalyzer(SampleRate=fs,AveragingMethod="running");
for i = 1:100
    data = sdr.rx();
    if isempty(data)
        continue
    end
    sa(data);
end