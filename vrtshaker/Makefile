BIN:=bin
PKGS:=
TARGETS:=

include $(shell $(CXX) -dumpmachine | sed "s/.*-//").mk

all: targets

#------------------------------------------------------------------------------

$(BIN)/launch_bin2dash.exe: \
	$(BIN)/src/launch_bin2dash.cpp.o \

TARGETS+=$(BIN)/launch_bin2dash.exe

$(BIN)/launch_sub.exe: \
	$(BIN)/src/launch_sub.cpp.o \
	
TARGETS+=$(BIN)/launch_sub.exe

#------------------------------------------------------------------------------

targets: $(TARGETS)

clean:
	rm -rf $(BIN)

$(BIN)/%.exe:
	@mkdir -p $(dir $@)
	$(CXX) -o "$@" $^ $(LDFLAGS)

$(BIN)/%.cpp.o: %.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c -o "$@" $<
