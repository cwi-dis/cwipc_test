#!/usr/bin/python2.7

import atexit, subprocess, time

processes = []

def exit_handler():
	for proc in processes:
		proc.kill()

atexit.register(exit_handler)

frameRate = 10
frameSize = 50000
segDurInMs = 4000
numSubSamples = 1000
hostnameAndPort = "127.0.0.1:9000"

processes.append(subprocess.Popen(["evanescent.exe"]))
processes.append(subprocess.Popen(["bin/launch_bin2dash.exe", str(frameRate), str(frameSize), str(segDurInMs), "http://%s/" % hostnameAndPort]))
time.sleep(3 * segDurInMs / 1000)

launch_sub = subprocess.Popen(["bin/launch_sub.exe", str(numSubSamples), "http://%s/vrtogether.mpd" % hostnameAndPort], stdout=subprocess.PIPE)
processes.append(launch_sub)

hasLines = False
for line in iter(launch_sub.stdout.readline, ""):
	line = line.rstrip()
	hasLines = True
        print("Latency: " + line + " s")

if not hasLines:
	raise ValueError('SUB did not get any data')
