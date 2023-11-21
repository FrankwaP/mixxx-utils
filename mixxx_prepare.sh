#!/bin/bash

# we use the recommendantions from this page:
# https://github.com/mixxxdj/mixxx/wiki/Adjusting-Audio-Latency


# the commands needs to be called with sudo
[ "$UID" -eq 0 ] || exec sudo bash "$0" "$@"

# CPU frequency scaling is a main cause of Mixxx skipping on laptops.
echo "Disabling CPU frequency scaling"
for i in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
	echo performance > $i
done

# Simultaneous Multithreading (SMT), or HyperThreading (HT) as Intel calls it,
# can make some programs faster but makes realtime audio software
# like Mixxx much more likely to glitch.
echo "Disabling hyperthreading"
echo off > /sys/devices/system/cpu/smt/control


# ATTENTION: this is an extra for my personnal use
# I use GenyMotion which does not stops Android Debug Bridge when it's closed
pgrep adb && echo "Killing Android Debug Bridge" && killall adb


