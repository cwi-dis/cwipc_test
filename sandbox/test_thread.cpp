//
// Very simple program to test how many thread creations we can do per second.
// 
// Build with `c++ -std=c++11 test_thread.cpp` or drop into a VS Windows console app.
//
#include <time.h>
#include <iostream>
#include <thread>

int64_t counter;

void inc() {
	counter++;
}

void threadinc() {
	std::thread mythread = std::thread([] { counter++; });
	mythread.join();
}

typedef void (*funcptr)();

void runtest(std::string name, funcptr func) {
	counter = 0;
	time_t pre_start = time(NULL);
	time_t start = time(NULL);
	while (start == pre_start) {
		start = time(NULL);
	}
	time_t stop = time(NULL);
	while (stop == start) {
		func();
		stop = time(NULL);
	}
	std::cout << name << ": " << counter << " per second" << std::endl;
}
	
int main() {
	runtest("direct call", inc);
	runtest("threaded call", threadinc);
	return 0;
}
