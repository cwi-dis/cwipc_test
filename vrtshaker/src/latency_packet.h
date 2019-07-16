#pragma once

struct LatencyPacket
{
  int64_t timeNow; // in ms
  int64_t sequenceNumber;
};

auto const MAX_BUF_SIZE = 10 * 1024 * 1024;

#ifdef _WIN32

#include <windows.h>

static HMODULE safeLoad(const char* name) {
  auto r = LoadLibrary(name);
  if(!r) {
		char msg[256];
		sprintf(msg, "Can't load '%s': %s", name, std::to_string(GetLastError()).c_str());
		throw std::runtime_error(msg);
  }
  return r;
}

static void* safeImport(HMODULE lib, const char* name) {
	auto r = (void*)GetProcAddress(lib, name);
	if (!r)
		throw std::runtime_error("Symbol not found: " + std::string(name));
	return r;
}

#define safeUnload FreeLibrary

#else

#include <SDL.h>

#undef main

static void* safeImport(void* lib, const char* name) {
	auto r = SDL_LoadFunction(lib, name);
	if (!r)
		throw std::runtime_error("Symbol not found: " + std::string(name));

	return r;
}

static void* safeLoad(const char* name) {
  auto r = SDL_LoadObject(name);
  if(!r)
		throw std::runtime_error("Can't load '" + std::string(name) + "' : " + SDL_GetError() );

  return r;
}

#define safeUnload SDL_UnloadObject

#endif

#define IMPORT(name) ((decltype(name)*)safeImport(lib, # name))

