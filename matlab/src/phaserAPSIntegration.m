% Clear
clear;
close all;
clc;

%% Create remote phaser with APS service

id = 'fake-phaser-001';
apsService = aps.ApsClientService(id);
sdr = phaser.RemotePhaser(id,ClientService=apsService);

%% Generate some data

data = sdr.rx();