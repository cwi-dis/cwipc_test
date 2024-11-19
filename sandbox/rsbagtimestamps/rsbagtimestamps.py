import sys
import argparse
from typing import List, Any, Tuple, TextIO
import pyrealsense2 as rs
import time

class BagPipeline:

    def __init__(self, camnum : int, filename: str, args : argparse.Namespace):
        self.debug = args.debug
        self.nodepth = args.nodepth
        self.nocolor = args.nocolor
        self.multisync = args.multisync
        self.camnum = camnum
        self.filename = filename
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        rs.config.enable_device_from_file(self.config, self.filename)
        if not self.nodepth:
            self.config.enable_stream(rs.stream.depth, rs.format.z16, 0)
        if not self.nocolor:
            self.config.enable_stream(rs.stream.color, rs.format.rgb8, 0)
        self.profile = self.config.resolve(self.pipeline)
        self.depth_fps = 0 if self.nodepth else self.profile.get_stream(rs.stream.depth).fps()
        self.color_fps = 0 if self.nocolor else self.profile.get_stream(rs.stream.color).fps()
        self.wanted_depth_duration = 0 if self.nodepth else int(1000.0 / self.depth_fps)
        self.wanted_color_duration = 0 if self.nocolor else int(1000.0 / self.color_fps)
        print(f"{self.filename}: camera={self.camnum} color_fps={self.color_fps} ({self.wanted_color_duration} ms), depth_fps={self.depth_fps} ({self.wanted_depth_duration} ms)", file=sys.stderr)
        
        if args.realtime:
            self.pipeline.start(self.config)
            self.framesource = self.pipeline
        else:
            if args.syncer:
                self.syncer = rs.syncer(10)
                self.pipeline.start(self.config, self.syncerfeed)
                self.framesource = self.syncer
            else:
                self.pipeline.start(self.config)
                self.framesource = self.pipeline

            playback = self.pipeline.get_active_profile().get_device().as_playback()
            playback.set_real_time(False)

        self.current_depth_timestamp = 0
        self.current_color_timestamp = 0
        self.current_frame_timestamp = 0
        self.current_depth_duration = 0
        self.current_color_duration = 0
        self.current_frame_duration = 0
        self.current_late_ms = 0
        self.current_skipped_ms = 0
        self.current_frames = None

    def syncerfeed(self, frame):
        print("xxxjack got frame")
        self.syncer(frame)

    def nextframe(self, earliest_timestamp : int) -> bool:
        loopcount = 0
        self.current_late_ms = 0
        self.current_skipped = 0
        depth_duration_consumed = 0
        if self.debug: print(f"xxxjack cam {self.camnum} earliest {earliest_timestamp} current {self.current_frame_timestamp}", file=sys.stderr)
        while earliest_timestamp == 0 or self.current_frame_timestamp <= earliest_timestamp:
            loopcount += 1
            frames = self.framesource.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if self.nodepth:
                depth_timestamp = color_timestamp = int(color_frame.get_timestamp())
            elif self.nocolor:
                color_timestamp = depth_timestamp = int(depth_frame.get_timestamp())
            else:
                depth_timestamp = int(depth_frame.get_timestamp())
                color_timestamp = int(color_frame.get_timestamp())

            if self.debug: print(f"xxxjack cam {self.camnum} dts={depth_timestamp} cts={color_timestamp}", file=sys.stderr)
            if self.current_depth_timestamp != 0 and depth_timestamp < self.current_depth_timestamp:
                print(f"{self.filename}: Depth recording stopped at {self.current_depth_timestamp} {time.ctime(self.current_depth_timestamp/1000)}", file=sys.stderr)
                return False
            if self.current_color_timestamp != 0 and color_timestamp < self.current_color_timestamp:
                print(f"{self.filename}: Color recording stopped at {self.current_color_timestamp} {time.ctime(self.current_color_timestamp/1000)}", file=sys.stderr)
                return False
            if self.current_depth_timestamp == 0:
                print(f"{self.filename}: Depth recording started at {depth_timestamp} {time.ctime(depth_timestamp/1000)}", file=sys.stderr)
                self.current_depth_timestamp = depth_timestamp
            if self.current_color_timestamp == 0:
                print(f"{self.filename}: Color recording started at {color_timestamp} {time.ctime(color_timestamp/1000)}", file=sys.stderr)
                self.current_color_timestamp = color_timestamp
            self.current_depth_duration = depth_timestamp - self.current_depth_timestamp
            depth_duration_consumed += self.current_depth_duration
            self.current_color_duration = color_timestamp - self.current_color_timestamp
            self.current_depth_timestamp = depth_timestamp
            self.current_color_timestamp = color_timestamp
            current_frame_timestamp = max(depth_timestamp, color_timestamp)
            self.current_frame_duration = current_frame_timestamp - self.current_frame_timestamp
            self.current_frame_timestamp = current_frame_timestamp
            if earliest_timestamp == 0:
                break
            if not self.multisync:
                break
        self.current_late_ms = earliest_timestamp - self.current_frame_timestamp
        if self.current_late_ms < 0:
            self.current_late_ms = 0
        if self.current_late_ms > 0:
            print(f"Camera {self.camnum}: Late {self.current_late_ms} ms", file=sys.stderr)
        if loopcount > 1:
            print(f"Camera {self.camnum}: Skipped {loopcount-1} frames, {depth_duration_consumed-self.current_depth_duration} ms, around ts={self.current_frame_timestamp}", file=sys.stderr)
            self.current_skipped_ms = depth_duration_consumed-self.current_depth_duration
        else:
            self.current_skipped_ms = 0
        return True

    def get_frames(self) -> Any:
        return self.current_frames
    
    def get_timestamps(self) -> Tuple[int, int, int]:
        return self.current_frame_timestamp, self.current_depth_timestamp, self.current_color_timestamp

    def get_durations(self) -> Tuple[int, int, int]:
        return self.current_frame_duration, self.current_depth_duration, self.current_color_duration

    def get_resync_params(self) -> Tuple[int, int]:
        return self.current_late_ms, self.current_skipped_ms
    
def main():
    parser = argparse.ArgumentParser(sys.argv[0], "Print timestamps from recorded realsense bag file")
    parser.add_argument("--concurrent", default=False, action="store_true", help="Attempt to synchronise files. Implies --stdout")
    parser.add_argument("--stdout", default=False, action="store_true", help="Send CSV data to stdout. Default: per-camera output in ts-BAGFILE.csv")
    parser.add_argument("--realtime", action="store_true", help="Use librealsense set_real_time(true) for realtime playback")
    parser.add_argument("--syncer", action="store_true", help="Use librealsense rs2::syncer to sync RGB and D streams")
    parser.add_argument("--multisync", action="store_true", help="Attempt multi-camera sync (for --concurrent)")
    parser.add_argument("--nocolor", action="store_true", help="Ignore color frames")
    parser.add_argument("--nodepth", action="store_true", help="Ignore depth frames")
    parser.add_argument("--debug", action="store_true", help="Print debug messages")

    parser.add_argument("bagfile", nargs="*", help="File(s) to print timestamps from")
    args = parser.parse_args()
    if args.concurrent:
        printstamps(args.bagfile, args)
    else:
        for bf in args.bagfile:
            print(f"{bf}:", file=sys.stderr)
            printstamps([bf], args)

def printstamps(filenames : List[str], args : argparse.Namespace) -> None:
    readers : List[BagPipeline]= []
    csv_output : TextIO
    if args.stdout or len(filenames) > 1:
        csv_output = sys.stdout
    else:
        csv_name = f"ts-{filenames[0]}.csv"
        csv_output = open(csv_name, "w")
    camnum = 0
    for filename in filenames:
        reader = BagPipeline(camnum, filename, args)
        readers.append(reader)
        camnum += 1
    master_cam = readers[0]
    del readers[0]
    recording_start_time = 0
    playback_start_time = time.time()
    print("camnum,timestamp,d_timestamp,c_timestamp,master_d_offset,mslate,msskipped,rgb_d_offset,dur,d_dur,rgb_dur", file=csv_output)
    earliest_next_timestamp = 0
    while True:
        ok = master_cam.nextframe(earliest_next_timestamp)
        if not ok:
            break
        _ = master_cam.get_frames()
        master_frame_timestamp, master_depth_timestamp, master_color_timestamp = master_cam.get_timestamps()
        frame_duration, depth_duration, color_duration = master_cam.get_durations()
        mslate, msskipped = master_cam.get_resync_params()
        print(f"0,{master_frame_timestamp},{master_depth_timestamp},{master_color_timestamp},0,{mslate},{msskipped},{master_depth_timestamp-master_color_timestamp},{frame_duration},{depth_duration},{color_duration}", file=csv_output)
        earliest_next_timestamp = master_frame_timestamp
        if recording_start_time == 0:
            recording_start_time = master_frame_timestamp
        cam_index = 0
        for cam in readers:
            cam_index += 1
            ok = cam.nextframe(earliest_next_timestamp)
            if not ok:
                print(f"Camera {cam_index} hit EOF early", file=sys.stderr)
                break
            _ = cam.get_frames()
            frame_timestamp, depth_timestamp, color_timestamp = cam.get_timestamps()
            frame_duration, depth_duration, color_duration = cam.get_durations()
            mslate, msskipped = cam.get_resync_params()
            print(f"{cam_index},{frame_timestamp},{depth_timestamp},{color_timestamp},{depth_timestamp-master_depth_timestamp},{mslate},{msskipped},{depth_timestamp-color_timestamp},{frame_duration},{depth_duration},{color_duration}", file=csv_output)
            if depth_timestamp > master_depth_timestamp + depth_duration:
                print(f"Camera {cam_index}: Adjust earliest_next_timestamp to {depth_timestamp} (delta={depth_timestamp-earliest_next_timestamp})", file=sys.stderr)
                earliest_next_timestamp = depth_timestamp
    recording_duration = (earliest_next_timestamp - recording_start_time) / 1000
    playback_duration = time.time() - playback_start_time
    print(f"Recording duration: {int(recording_duration)} seconds. Playback duration: {int(playback_duration)} seconds", file=sys.stderr)
        
if __name__ == "__main__":
    main()
