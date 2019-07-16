// Copyright (C) 2019 Motion Spell
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.

#include <chrono>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#include "signals_unity_bridge.h"
#include "latency_packet.h"

void launchSub(int numSamples, const char *mediaUrl) {
	auto const libraryPath = "signals-unity-bridge.so";
	auto lib = safeLoad(libraryPath);

	auto func_sub_create = IMPORT(sub_create);
	auto func_sub_play = IMPORT(sub_play);
	auto func_sub_destroy = IMPORT(sub_destroy);
	auto func_sub_grab_frame = IMPORT(sub_grab_frame);
	auto func_sub_get_stream_count = IMPORT(sub_get_stream_count);

	auto handle = func_sub_create("MyMediaPipeline");
	if (!handle)
		throw std::runtime_error("SUB: cannot create");

	if (!func_sub_play(handle, mediaUrl))
		throw std::runtime_error("SUB: play URL failed");

	if (func_sub_get_stream_count(handle) == 0)
		throw std::runtime_error("No streams found");

	int64_t lastSeqNum = -1;
	std::vector<uint8_t> buf(MAX_BUF_SIZE);
	auto pkt = (LatencyPacket*)buf.data();
	while (numSamples > 0) {
		FrameInfo info{};
		auto size = func_sub_grab_frame(handle, 0, buf.data(), buf.size(), &info);

		if (size == 0) {
			std::this_thread::sleep_for(std::chrono::milliseconds(1)); //sleep as little as possible
		} else {
			if (size < 8)
				throw std::runtime_error("Invalid data size < 8");

			if(pkt->sequenceNumber != lastSeqNum + 1)
				fprintf(stderr, "Warning: missed packets\n");

			lastSeqNum = pkt->sequenceNumber;

			auto now = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();
			printf("%.2f\n", (now - pkt->timeNow)/1000.0);
			fflush(stdout);
			numSamples--;
		}
	}

	func_sub_destroy(handle);
	safeUnload(lib);
}

int main(int argc, char const* argv[]) {
	try {
		if (argc != 3) {
			fprintf(stderr, "Usage: %s numSamples mediaUrl\n", argv[0]);
			return 1;
		}

		auto numSamples = atoi(argv[1]);
		auto mediaUrl = argv[2];
		fprintf(stderr, "[%s] Detected: numSamples=%d mediaUrl=%s\n", argv[0], numSamples, mediaUrl);

		launchSub(numSamples, mediaUrl);

		fprintf(stderr, "[%s] OK\n", argv[0]);
		return 0;
	} catch (std::exception const &e) {
		fprintf(stderr, "[%s] Fatal: %s\n", argv[0], e.what());
		return 1;
	}
}
