% Clear
clear;
close all;
clc;

%% Create remote phaser

id = 'fake-phaser-001';
sdr = phaser.RemotePhaser(id);

%% Time run

tic
for i = 1:100
    sdr.rx();
end
toc

%% Find HB100 Fc

f_start = 10.2e9;
f_stop = 10.6e9;
f_step = 10e6;
f_test = f_start:f_step:f_stop;
nsamples = 100;
nfreqs = length(f_test);
ax = axes(figure);
hold(ax,"on");
set(sdr,'rx_buffer_size',nsamples);
allfreqs = zeros(nfreqs,nsamples);
allresps = zeros(nfreqs,nsamples);

for iFreq = 1:nfreqs
    fc = f_test(iFreq);
    set(sdr,'operating_frequency',fc);
    data = sdr.rx();
    fs = get(sdr,'sample_rate');
    fspanStart = -fs/2;
    fstep = fs/nsamples;
    fspanStop = fs/2-fstep;
    fspan = fc-(fspanStart:fstep:fspanStop);
    resp = mag2db(fftshift(abs(fft(data(:,1)))));
    allfreqs(iFreq,:) = fspan;
    allresps(iFreq,:) = resp;
    plot(ax,fspan,resp);
    drawnow;
end

freq = allfreqs(allresps == max(allresps,[],"all"));

%% Run the receiver at the HB100 frequency

nruns = 100;
nsamples = 100;
set(sdr,'rx_buffer_size',nsamples);
set(sdr,'operating_frequency',freq);
ax = axes(figure);

for iRun = 1:nruns
    data = sdr.rx();
    fs = get(sdr,'sample_rate');
    fspanStart = -fs/2;
    fstep = fs/nsamples;
    fspanStop = fs/2-fstep;
    fspan = freq-(fspanStart:fstep:fspanStop);
    resp = mag2db(fftshift(abs(fft(data(:,1)))));
    plot(ax,fspan,resp);
    drawnow;
end