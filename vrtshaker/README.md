# Build

CXXFLAGS+="-I/path/to/sub-31 -I/path/to/pcl2dash-20" \
make -j

# Launch

SIGNALS_SMD_PATH=/path/to/sub-31/platform \
PATH=$PATH:/path/to/evanescent-1 \
LD_LIBRARY_PATH=/path/to/evanescent-1/platform:/path/to/sub-31/platform:/path/to/pcl2dash-20/platform \
./run.py
