import sys
import argparse
from typing import List, Any, Tuple
import pyrealsense2 as rs
import time

class BagPipeline:

    def __init__(self, filename: str):
        self.filename = filename
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        rs.config.enable_device_from_file(self.config, self.filename)
        self.config.enable_stream(rs.stream.depth, rs.format.z16, 0)
        self.config.enable_stream(rs.stream.color, rs.format.rgb8, 0)
        self.profile = self.config.resolve(self.pipeline)
        self.depth_fps = self.profile.get_stream(rs.stream.depth).fps()
        self.color_fps = self.profile.get_stream(rs.stream.color).fps()
        self.wanted_depth_duration = int(1000.0 / self.depth_fps)
        self.wanted_color_duration = int(1000.0 / self.color_fps)
        print(f"color_fps={self.color_fps} ({self.wanted_color_duration} ms), depth_fps={self.depth_fps} ({self.wanted_depth_duration} ms)")
        self.pipeline.start(self.config)
        self.current_depth_timestamp = 0
        self.current_color_timestamp = 0
        self.current_depth_duration = 0
        self.current_color_duration = 0
        self.current_frames = None

    def nextframe(self, earliest_timestamp : int) -> bool:
        while earliest_timestamp == 0 or earliest_timestamp > self.current_depth_timestamp:
            frames = self.pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            depth_timestamp = int(depth_frame.get_timestamp())
            color_timestamp = int(color_frame.get_timestamp())
            if self.current_depth_timestamp != 0 and depth_timestamp < self.current_depth_timestamp:
                print(f"{self.filename}: Depth recording stopped at {time.ctime(self.current_depth_timestamp/1000)}")
                return False
            if self.current_color_timestamp != 0 and color_timestamp < self.current_color_timestamp:
                print(f"{self.filename}: Color recording stopped at {time.ctime(self.current_color_timestamp/1000)}")
                return False
            if self.current_depth_timestamp == 0:
                print(f"{self.filename}: Depth recording started at {time.ctime(depth_timestamp/1000)}")
                self.current_depth_timestamp = depth_timestamp
            if self.current_color_timestamp == 0:
                print(f"{self.filename}: Color recording started at {time.ctime(color_timestamp/1000)}")
                self.current_color_timestamp = color_timestamp
            self.current_depth_duration = depth_timestamp - self.current_depth_timestamp
            self.current_color_duration = color_timestamp - self.current_color_timestamp
            self.current_depth_timestamp = depth_timestamp
            self.current_color_timestamp = color_timestamp
            earliest_timestamp = self.current_depth_timestamp
        return True

    def get_frames(self) -> Any:
        return self.current_frames
    
    def get_timestamps(self) -> Tuple[int, int]:
        return self.current_depth_timestamp, self.current_color_timestamp

    def get_durations(self) -> Tuple[int, int]:
        return self.current_depth_duration, self.current_color_duration

def main():
    parser = argparse.ArgumentParser(sys.argv[0], "Print timestamps from recorded realsense bag file")
    parser.add_argument("bagfile", help="File to print timestamps from")
    args = parser.parse_args()
    printstamps([args.bagfile])

def printstamps(filenames : List[str]) -> None:
    bagpipeline = BagPipeline(filenames[0])
    print("rgb_d_offset,d_dur,rgb_dur")
    earliest_next_timestamp = 0
    while True:
        ok = bagpipeline.nextframe(earliest_next_timestamp)
        if not ok:
            break
        frames = bagpipeline.get_frames()
        depth_timestamp, color_timestamp = bagpipeline.get_timestamps()
        depth_duration, color_duration = bagpipeline.get_durations()
        print(f"{depth_timestamp-color_timestamp}, {depth_duration}, {color_duration}")
        earliest_next_timestamp = depth_timestamp+1

if __name__ == "__main__":
    main()
