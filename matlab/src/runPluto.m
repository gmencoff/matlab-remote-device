% Clear
clear;
close all;

%% Create remote pluto

id = 'mVDaisJOlg';
sdr = pluto.RemotePluto(id);

%% Sequential Receive

fs = get(sdr,'sample_rate');
sa = spectrumAnalyzer(SampleRate=fs,AveragingMethod="running");
tic
for i = 1:50
    data = sdr.rx();
    if isempty(data)
        continue
    end
    sa(data);
end
toc

%% Stream receive

sdr.startRxStream(60);
fs = get(sdr,'sample_rate');
sa = spectrumAnalyzer(SampleRate=fs,AveragingMethod="running");
tic
for i = 1:50
    data = sdr.getStreamData();
    if isempty(data)
        continue
    end
    sa(data);
end
toc