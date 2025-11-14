% Clear
clear;
close all;
clc;

%% Create remote pluto

id = 'fake-phaser-001';
sdr = phaser.RemotePhaser(id);