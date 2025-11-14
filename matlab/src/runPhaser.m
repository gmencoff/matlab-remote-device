% Clear
clear;
close all;
clc;

%% Create remote phaser

id = 'pNjYuHKCaF';
sdr = phaser.RemotePhaser(id);

%% Find HB100 Fc

f_start = 10.2e9;
f_stop = 10.6e9;
f_step = 5e6;
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
    allfreqs(iFreq,:) = fspan;
    allresps(iFreq,:) = mag2db(fftshift(abs(fft(data(:,1))))); % Store the received data for the current frequency
end

plot(allfreqs',allresps');
freq = allfreqs(allresps == max(allresps,[],"all"));