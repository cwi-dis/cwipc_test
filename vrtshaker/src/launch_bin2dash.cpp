// Copyright (C) 2019 Motion Spell
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#include "bin2dash.hpp"
#include "latency_packet.h"

void launchBin2dash(int segDurInMs, float frameRate, int frameSize, const char* publishUrl) {
	auto const libraryPath = "bin2dash.so";
	auto lib = safeLoad(libraryPath);

	auto func_vrt_create = IMPORT(vrt_create);
	auto func_vrt_destroy = IMPORT(vrt_destroy);
	auto func_vrt_push_buffer = IMPORT(vrt_push_buffer);

	auto handle = func_vrt_create("vrtogether", VRT_4CC('t', 'e', 's', 't'), publishUrl, segDurInMs, 0);
	if (!handle)
		throw std::runtime_error("SUB: cannot create");

	int64_t seqNum = 0;

	std::vector<uint8_t> buf(std::max<size_t>(sizeof(LatencyPacket), frameSize));
	auto initTime = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();
	while (1) { /*meant to be killed*/
		LatencyPacket pkt {};
		pkt.sequenceNumber = seqNum++;
		pkt.timeNow = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();
		memcpy(buf.data(), (uint8_t*)&pkt, sizeof pkt);
		func_vrt_push_buffer(handle, buf.data(), buf.size());

		/*regulation*/
		auto mediaTime = (int64_t)(1000 * pkt.sequenceNumber / frameRate);
		auto clockTime = pkt.timeNow - initTime;
		auto delay = mediaTime - clockTime;
		if (delay > 0) {
			fprintf(stderr, "Sleep %ldms\n", delay);
			std::this_thread::sleep_for(std::chrono::milliseconds(delay));
		} else if (delay < -1000)
			fprintf(stderr, "Running late from %ldms\n", -delay);
	}

	func_vrt_destroy(handle);
	safeUnload(lib);
}

int main(int argc, char const* argv[]) {
	try {
		if (argc != 5) {
			fprintf(stderr, "Usage: %s frameRate frameSize segDurInMs publishUrl\n", argv[0]);
			return 1;
		}

		auto frameRate = atof(argv[1]);
		auto frameSize = atoi(argv[2]);
		if (frameSize > MAX_BUF_SIZE) {
			fprintf(stderr, "[%s] frameSize can't be bigger than %d.\n", argv[0], MAX_BUF_SIZE);
			frameSize = MAX_BUF_SIZE;
		}
		auto segDurInMs = atoi(argv[3]);
		auto publishUrl = argv[4];
		fprintf(stderr, "[%s] Detected: segDurInMs=%d frameRate=%f frameSize=%d publishUrl=%s\n", argv[0], segDurInMs, frameRate, frameSize, publishUrl);

		launchBin2dash(segDurInMs, frameRate, frameSize, publishUrl);

		fprintf(stderr, "[%s] OK\n", argv[0]);
		return 0;
	} catch (std::exception const &e) {
		fprintf(stderr, "[%s] Fatal: %s\n", argv[0], e.what());
		return 1;
	}
}
