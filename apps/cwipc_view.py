import sys
import os
import signal
import threading
import time
import argparse
import traceback
import queue
import cwipc
import cwipc.codec
import cwipc.realsense2

# Convoluted code warning: adding ../python directory to path so we can import subsource
_sourcedir = os.path.dirname(__file__)
_sourcedir = os.path.realpath(_sourcedir)
_pardir = os.path.dirname(_sourcedir)
_pythondir = os.path.join(_pardir, 'python')
sys.path.append(_pythondir)

import certhsource

def _dump_app_stacks(*args):
    print("pc_echo: QUIT received, dumping all stacks, %d threads:" % len(sys._current_frames()), file=sys.stderr)
    for threadId, stack in list(sys._current_frames().items()):
        print("\nThreadID:", threadId, file=sys.stderr)
        traceback.print_stack(stack, file=sys.stderr)
        print(file=sys.stderr)

class Visualizer:
    def __init__(self, verbose=False):
        self.visualiser = None
        self.producer = None
        self.queue = queue.Queue(maxsize=2)
        self.verbose = verbose
        self.start_window()
        
    def set_producer(self, producer):
        self.producer = producer    
        
    def run(self):
        while self.producer and self.producer.is_alive():
            try:
                pc = self.queue.get(timeout=0.033)
                ok = self.draw_pc(pc)
                if not ok: break
            except queue.Empty:
                pass
        
    def feed(self, pc):
        try:
            self.queue.put(pc)
        except queue.Full:
            pc.free()
            
    def start_window(self):
        self.visualiser = cwipc.cwipc_window("pc_echo")
        if self.verbose: print('display: started', flush=True)
        self.visualiser.feed(None, True)

    def draw_pc(self, pc):
        """Draw open3d pointcloud"""
        if pc:
            ok = self.visualiser.feed(pc, True)
            pc.free()
            if not ok: 
                print('display: window.feed() returned False')
                return False
        if self.visualiser.interact(None, "q", 30) == "q":
            return False
        return True

class SourceServer:
    def __init__(self, grabber, viewer=None, count=None, verbose=False):
        self.verbose = verbose
        self.grabber = grabber
        self.viewer = viewer
        self.count = count
        self.times_grab = []
        self.pointcounts_grab = []
        self.stopped = False
        self.lastGrabTime = None
        self.fps = None
        
    def __del__(self):
        self.stopped = True
        if self.grabber:
            self.grabber.free()
        del self.grabber

    def stop(self):
        if self.stopped: return
        if self.verbose: print("grab: stopping", flush=True)
        self.stopped = True
        if self.grabber:
            self.grabber.free()
            self.grabber = None
        
    def grab_pc(self):
        if self.lastGrabTime and self.fps:
            nextGrabTime = self.lastGrabTime + 1/self.fps
            if time.time() < nextGrabTime:
                time.sleep(nextGrabTime - time.time())
        pc = self.grabber.get()
        self.lastGrabTime = time.time()
        return pc
        
    def run(self):
        if self.verbose: print('grab: started', flush=True)
        while not self.stopped:
            t0 = time.time()
            pc = self.grab_pc()
            if not pc:
                print('grab: pointcloud==None')
                continue
            else:
                self.pointcounts_grab.append(pc.count())
                if self.verbose: print(f'grab: captured {pc.count()} points')
                t1 = time.time()
                if self.viewer: self.viewer.feed(pc)
            self.times_grab.append(t1-t0)
            if self.count != None:
                self.count -= 1
                if self.count <= 0:
                    break
        if self.verbose: print('grab: stopped', flush=True)
            
    def statistics(self):
        self.print1stat('capture_duration', self.times_grab)
        self.print1stat('capture_pointcount', self.pointcounts_grab, isInt=True)
        
    def print1stat(self, name, values, isInt=False):
        count = len(values)
        if count == 0:
            print('grab: {}: count=0'.format(name))
            return
        minValue = min(values)
        maxValue = max(values)
        avgValue = sum(values) / count
        if isInt:
            fmtstring = 'grab: {}: count={}, average={:.3f}, min={:d}, max={:d}'
        else:
            fmtstring = 'grab: {}: count={}, average={:.3f}, min={:.3f}, max={:.3f}'
        print(fmtstring.format(name, count, avgValue, minValue, maxValue))

def main():
    global ISSUE_20
    if hasattr(signal, 'SIGQUIT'):
        signal.signal(signal.SIGQUIT, _dump_app_stacks)
    parser = argparse.ArgumentParser(description="View pointcloud streams")
    parser.add_argument("--synthetic", action="store_true", help="View synthetic pointcloud in stead of realsense2 camera")
    parser.add_argument("--certh", action="store", metavar="URL", help="View Certh pointcloud in stead of realsense2 camera, captured from Rabbitmq server URL")
    parser.add_argument("--data", action="store", metavar="NAME", help="Use NAME for certh data exchange (default: VolumetricData)", default="VolumetricData")
    parser.add_argument("--metadata", action="store", metavar="NAME", help="Use NAME for certh metadata exchange (default: VolumetricMetaData)", default="VolumetricMetaData")
    parser.add_argument("--count", type=int, action="store", metavar="N", help="Stop after receiving N pointclouds")
    parser.add_argument("--display", action="store_true", help="Display each pointcloud after it has been received")
    parser.add_argument("--savecwicpc", action="store", metavar="DIR", help="Save compressed pointclouds to DIR")
    parser.add_argument("--verbose", action="store_true", help="Print information about each pointcloud after it has been received")
    args = parser.parse_args()
    #
    # Create source
    #
    if args.synthetic:
        source = cwipc.cwipc_synthetic()
    elif args.certh:
        source = certhsource.cwipc_certh(args.certh, args.data, args.metadata)
    else:
        source = cwipc.realsense2.cwipc_realsense2()

    if args.display:
        visualizer = Visualizer(args.verbose)
    else:
        visualizer = None

    sourceServer = SourceServer(source, visualizer, count=args.count, verbose=args.verbose)
    sourceThread = threading.Thread(target=sourceServer.run, args=())
    if visualizer:
        visualizer.set_producer(sourceThread)

    #
    # Run everything
    #
    try:
        sourceThread.start()

        if visualizer:
            visualizer.run()
            sourceServer.stop()
            
        sourceThread.join()
    except KeyboardInterrupt:
        print("Interrupted.")
        sourceServer.stop()
    except:
        traceback.print_exc()
    
    #
    # It is safe to call join (or stop) multiple times, so we ensure to cleanup
    #
    sourceServer.stop()
    sourceThread.join()
    sourceServer.statistics()
    
if __name__ == '__main__':
    main()
    
    
    
