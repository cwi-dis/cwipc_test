import sys
import argparse
from typing import List
import pyrealsense2 as rs
import time

def main():
    parser = argparse.ArgumentParser(sys.argv[0], "Print timestamps from recorded realsense bag file")
    parser.add_argument("bagfile", help="File to print timestamps from")
    args = parser.parse_args()
    printstamps([args.bagfile])

def printstamps(filenames : List[str]) -> None:
    pipeline = rs.pipeline()
    config = rs.config()
    for fn in filenames:
        rs.config.enable_device_from_file(config, fn)
    config.enable_stream(rs.stream.depth, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, rs.format.rgb8, 30)
    profile = config.resolve(pipeline)
    pipeline.start(config)
    prev_depth_timestamp = 0
    prev_color_timestamp = 0
    print("rgb_d_offset,d_dur,rgb_dur")
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        depth_timestamp = depth_frame.get_timestamp()
        color_timestamp = color_frame.get_timestamp()
        if prev_depth_timestamp != 0 and depth_timestamp < prev_depth_timestamp:
            print(f"Depth recording stopped at {time.ctime(prev_depth_timestamp/1000)}")
            break
        if prev_color_timestamp != 0 and color_timestamp < prev_color_timestamp:
            print(f"Color recording stopped at {time.ctime(prev_color_timestamp/1000)}")
            break
        print(f"{depth_timestamp-color_timestamp}, {depth_timestamp-prev_depth_timestamp}, {color_timestamp-prev_color_timestamp}")
        if prev_depth_timestamp == 0:
            print(f"Depth recording started at {time.ctime(depth_timestamp/1000)}")
        if prev_color_timestamp == 0:
            print(f"Color recording started at {time.ctime(color_timestamp/1000)}")
        prev_depth_timestamp = depth_timestamp
        prev_color_timestamp = color_timestamp

if __name__ == "__main__":
    main()
