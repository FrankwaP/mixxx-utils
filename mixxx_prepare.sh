#!/bin/bash

# we use the recommendantions from this page:
# https://github.com/mixxxdj/mixxx/wiki/Adjusting-Audio-Latency

# the commands needs to be called with sudo
[ "$UID" -eq 0 ] || exec sudo bash "$0" "$@"

# CPU frequency scaling is a main cause of Mixxx skipping on laptops.
for i in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
	cpunum=$(echo $i | grep -Po "\d+")
	msg="Disabling CPU frequency scaling for CPU #$cpunum"
	test "$(cat $i)" = "performance" || echo $msg && echo "performance" > $i
done

# Simultaneous Multithreading (SMT), or HyperThreading (HT) as Intel calls it,
# can make some programs faster but makes realtime audio software
# like Mixxx much more likely to glitch.
i=/sys/devices/system/cpu/smt/control
msg="Disabling hyperthreading" 
test "$(cat $i)" = "on" && echo $msg && echo "off" > $i


