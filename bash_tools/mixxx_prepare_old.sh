#!/bin/bash

# we use the recommendantions from this page:
# https://github.com/mixxxdj/mixxx/wiki/Adjusting-Audio-Latency

function network {
	# parameter 1: on/off
	msg="Network is $1"
	nmcli networking "$1" > /dev/null && echo "$msg"
}

function scaling {
	# parameter 1: schedutil/performance
	grep -wL "$1" /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | while read -r gov; do
		cpunum=$(echo "$gov" | grep -Po "\d+")
		msg="Scaling for CPU #$cpunum is $1"
		echo "$1" > "$gov" && echo "$msg"
	done
}

function hyperthreading {
	# parameter 1: on/off
	ctl=/sys/devices/system/cpu/smt/control
	msg="Hyperthreading is $1"
	grep -wq "$1" $ctl || { echo "$1" > "$ctl" && echo "$msg"; }
}


if [ $# -ne 1 ]; then
	echo "Needs one parameter: on/off"
    exit 1
fi


[ "$UID" -eq 0 ] || exec sudo bash "$0" "$@"
case $1 in
	on)
		network "off"
		scaling "performance"
		hyperthreading "off"
		;;
	off)
		network "on"
		scaling "schedutil"
		hyperthreading "on"
		;;
	*)
		echo "Needs one parameter: on/off"
esac
