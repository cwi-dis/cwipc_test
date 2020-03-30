import sys
import os
import time
import socket
import argparse
import traceback
import signal
import subprocess
import threading
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

from bin2dash import CpcBin2dashSink
from subsource import CpcSubSource

# NOTE: open3d must be imported after all the DLLs have been loaded (sigh)
import numpy as np
import open3d

def _dump_app_stacks(*args):
    print("pc_echo: QUIT received, dumping all stacks, %d threads:" % len(sys._current_frames()), file=sys.stderr)
    for threadId, stack in list(sys._current_frames().items()):
        print("\nThreadID:", threadId, file=sys.stderr)
        traceback.print_stack(stack, file=sys.stderr)
        print(file=sys.stderr)

def cwipc_to_o3d(pc):
    """Convert cwipc pointcloud to open3d pointcloud"""
    # Note that this method is inefficient, it can probably be done
    # in-place with some numpy magic
    pcpoints = pc.get_points()
    points = []
    colors = []
    for p in pcpoints:
        points.append((p.x, p.y, p.z))  
        colors.append((float(p.r)/255.0, float(p.g)/255.0, float(p.b)/255.0))
    points_v = open3d.Vector3dVector(points)
    colors_v = open3d.Vector3dVector(colors)
    rv = open3d.PointCloud()
    rv.points = points_v
    rv.colors = colors_v
    return rv

class Visualizer:
    def __init__(self, verbose=False):
        self.visualiser = None
        self.visualiser_o3dpc = None    
        self.producer = None
        self.queue = queue.Queue()
        self.verbose = verbose
        
    def set_producer(self, producer):
        self.producer = producer    
        
    def run(self):
        self.start_o3d()
        while self.producer and self.producer.is_alive():
            try:
                o3dpc = self.queue.get(timeout=1)
                self.draw_o3d(o3dpc)
            except queue.Empty:
                pass
        self.stop_o3d()
        
    def feed(self, pc):
        o3dpc = cwipc_to_o3d(pc)
        self.queue.put(o3dpc)
            
    def start_o3d(self):
        self.visualiser = open3d.Visualizer()
        self.visualiser.create_window(width=960, height=540)
        if self.verbose: print('display: started', flush=True)

    def draw_o3d(self, o3dpc):
        """Draw open3d pointcloud"""
        if self.visualiser_o3dpc == None:
            self.visualiser_o3dpc = o3dpc
            self.visualiser.add_geometry(o3dpc)
        else:
            self.visualiser_o3dpc.points = o3dpc.points
            self.visualiser_o3dpc.colors = o3dpc.colors
        if self.verbose: print('display:', len(self.visualiser_o3dpc.points), 'points', flush=True)
        self.visualiser.update_geometry()
        self.visualiser.update_renderer()
        self.visualiser.poll_events()
        
    def stop_o3d(self):
        self.visualiser.destroy_window()
        if self.verbose:print('display: stopped', flush=True)

class SourceServer:
    def __init__(self, bin2dash, *, fps=None, synthetic=False, tile=False, encparamlist=[], b2dparams={}, verbose=False):
        self.verbose = verbose
        self.fps = fps
        self.times_grab = []
        self.stopped = False
        self.lastGrabTime = None
        self.threads = []
        self.encoders = []
        self.transmitters = []
        self.encodergroup = None
        self.transmittergroup = None
                
        if synthetic:
            self.grabber = cwipc.cwipc_synthetic()
        else:
            self.grabber = cwipc.realsense2.cwipc_realsense2()
        
        if tile:
            self.tiles = []
            maxTile = self.grabber.maxtile()
            if self.verbose: print(f"grab: {maxTile} tiles")
            for i in range(maxTile):
                tileInfo = self.grabber.get_tileinfo_dict(i)
                if self.verbose: print(f"grab: tile {i}: {tileInfo}")
            self.tiles = range(0, maxTile)
            #self.tiles = range(1, maxTile)
        else:
            self.tiles = [0]
            
        self.encodergroup = cwipc.codec.cwipc_new_encodergroup()
        
        streamDescriptors = []
        for tilenum in self.tiles:
            for encparams in encparamlist:
                fourcc = 'cwi1'
                quality = 100*encparams.octree_bits + encparams.jpeg_quality
                streamDescriptors.append((fourcc, tilenum, quality))
        b2dparams['streamDescs'] = streamDescriptors
        
        self.transmittergroup = CpcBin2dashSink(bin2dash, **b2dparams)
        
        for tilenum in self.tiles:
            for encparams in encparamlist:
                encparams.tilenumber = tilenum
                if self.verbose:
                    idx = len(self.transmitters)
                    sd = streamDescriptors[idx]
                    print(f"grab: streamnum {idx}: tilenum={tilenum}={sd[1]}, quality={sd[2]}, octree_bits={encparams.octree_bits}, jpeg_quality={encparams.jpeg_quality}")
                enc = self.encodergroup.addencoder(params=encparams)
                self.encoders.append(enc)
                streamNum = len(self.transmitters)
                transmitter = Transmitter(enc, self.transmittergroup, streamNum, verbose=verbose)
                self.transmitters.append(transmitter)
                thr = threading.Thread(target=transmitter.run, args=())
                self.threads.append(thr)
        
        
    def __del__(self):
        self.stopped = True
        if self.grabber:
            self.grabber.free()
        if self.encodergroup:
            self.encodergroup.free()
        del self.grabber
        del self.encodergroup
        del self.transmitters
        del self.threads
        del self.encoders

    def stop(self):
        self.stopped = True
        for t in self.transmitters:
            t.stop()
        for t in self.threads:
            t.join()
        
    def grab_pc(self):
        if self.lastGrabTime and self.fps:
            nextGrabTime = self.lastGrabTime + 1/self.fps
            if time.time() < nextGrabTime:
                time.sleep(nextGrabTime - time.time())
        pc = self.grabber.get()
        self.lastGrabTime = time.time()
        return pc
        
    def run(self):
        for t in self.threads: t.start()
        sourceTime = 0
        if self.verbose: print('grab: started', flush=True)
        while not self.stopped:
            t0 = time.time()
            pc = self.grab_pc()
            sourceTime = pc.timestamp()
            t1 = time.time()
            self.encodergroup.feed(pc)
            pc.free()
            self.times_grab.append(t1-t0)
        if self.verbose: print('grab: stopped', flush=True)
            
    def statistics(self):
        self.print1stat('grab', self.times_grab)
        for t in self.transmitters:
            t.statistics()
        
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

class Transmitter:
    XMITNUM = 1
    
    def __init__(self, cpcsource, sink, stream_index, verbose=False):
        self.xmitNum = Transmitter.XMITNUM
        Transmitter.XMITNUM += 1
        self.verbose = verbose
        self.times_encode = []
        self.sizes_encode = []
        self.times_send = []
        self.startTime = None
        self.stopTime = None
        self.totalBytes = 0
        self.stopped = False
        self.cpcsource = cpcsource
        self.sink = sink
        self.stream_index = stream_index
        self.prevt3 = time.time()
        
    def stop(self):
        self.stopped = True
        
    def run(self):
        if self.verbose: print(f"send {self.xmitNum}: started", flush=True)
        while not self.stopped:
            cpc = self.waitforcpc()
            if not cpc:
                if self.verbose: print(f"send {self.xmitNum}: no compressed data available")
                continue
            self.sendcpc(cpc)
        if self.verbose: print(f"send {self.xmitNum}: stopped", flush=True)

    def waitforcpc(self):
        t1 = time.time()
        gotData = self.cpcsource.available(True)
        if not gotData: return None
        cpc = self.cpcsource.get_bytes()
        self.sizes_encode.append(len(cpc))
        t2 = time.time()
        self.times_encode.append(t2-t1)
        return cpc
    
    def sendcpc(self, cpc):
        self.totalBytes += len(cpc)
        self.sink.canfeed(time.time(), wait=True)
        t2 = time.time()
        if self.startTime == None: self.startTime = time.time()
        self.sink.feed(cpc, stream_index=self.stream_index)
        self.stopTime = time.time()
        t3 = time.time()
        self.times_send.append(t3-t2)
        if self.verbose: print(f"send {self.xmitNum}: {t3}: compressed size: {len(cpc)}, waited: {t3-self.prevt3}", flush=True)
        self.prevt3 = t3

    def statistics(self):
        self.print1stat('encode', self.times_encode)
        self.print1stat('encodedsize', self.sizes_encode, isInt=True)
        self.print1stat('send', self.times_send)
        if self.startTime and self.stopTime and self.startTime != self.stopTime:
            bps = self.totalBytes/(self.stopTime-self.startTime)
            scale = ''
            if bps > 10000:
                bps /= 1000
                scale = 'k'
            if bps > 10000:
                bps /= 1000
                scale = 'M'
            print(f'send {self.xmitNum}: bandwidth={bps:.0f} {scale}B/s')
        
    def print1stat(self, name, values, isInt=False):
        count = len(values)
        if count == 0:
            print(f'send {self.xmitNum}: {name}: count=0')
            return
        minValue = min(values)
        maxValue = max(values)
        avgValue = sum(values) / count
        if isInt:
            print(f'send {self.xmitNum}: {name}: count={count}, average={avgValue:.3f}, min={minValue:d}, max={maxValue:d}')
        else:
            print(f'send {self.xmitNum}: {name}: count={count}, average={avgValue:.3f}, min={minValue:.3f}, max={maxValue:.3f}')

class SinkClient:
    SINKNUM = 1
    
    def __init__(self, sub, count=None, delay=0, retry=0, display=False, savedir=None, verbose=False):
        self.sinkNum = SinkClient.SINKNUM
        SinkClient.SINKNUM += 1
        self.verbose = verbose
        if verbose: print(f"recv {self.sinkNum}: sub url={sub}", flush=True)
        self.source = CpcSubSource(sub)
        self.count = count
        self.delay = delay
        self.retry = retry
        self.display = display
        self.times_recv = []
        self.times_decode = []
        self.times_latency = []
        self.times_completeloop = []
        self.sizes_received = []
        self.savedir = savedir
        self.stopped = False
        self.startTime = None
        self.stopTime = None
        self.totalBytes = 0

    def stop(self):
        self.stopped = True
        
    def receiver_loop(self):
        seqno = 1
        while not self.stopped:
            t0 = time.time()
            if self.startTime == None: self.startTime = time.time()
            cpc = self.source.read_cpc()
            self.stopTime = time.time()
            if not cpc:
                if self.verbose: print(f"recv {self.sinkNum}: read_cpc() returned None", flush=True)
                break
            self.sizes_received.append(len(cpc))
            self.totalBytes += len(cpc)
            t1 = time.time()
            pc = self.decompress(cpc)
            if not pc:
                print(f"recv {self.sinkNum}: decompress({len(cpc)} bytes of compressed data) failed to produce a pointcloud")
            t2 = time.time()
            self.times_recv.append(t1-t0)
            self.times_decode.append(t2-t1)
            sinkTime = time.time()
            if pc:
                sourceTime = pc.timestamp() / 1000.0
                if self.verbose: print(f"recv {self.sinkNum}: {t1}: compressed size: {len(cpc)}, timestamp: {sourceTime}, waited: {t1-t0}, latency: {sinkTime-sourceTime}", flush=True)
                self.times_latency.append(sinkTime-sourceTime)
            if cpc and self.savedir:
                savefile = 'pointcloud-%05d.cwicpc' % seqno
                seqno += 1
                with open(os.path.join(self.savedir, savefile), 'wb') as fp:
                    fp.write(cpc)
            if pc and self.display and self.sinkNum == 1:
                self.display.feed(pc)
            if pc:
                pc.free()
            if self.count != None:
                self.count -= 1
                if self.count <= 0:
                    break
            t3 = time.time()
            self.times_completeloop.append(t3-t0)
            
    def decompress(self, cpc):
        decomp = cwipc.codec.cwipc_new_decoder()
        decomp.feed(cpc)
        gotData = decomp.available(True)
        if not gotData: return None
        pc = decomp.get()
        return pc
        
    def run(self):
        while True:
            if self.delay:
                time.sleep(self.delay)
                if self.verbose: print(f"recv {self.sinkNum}: starting", flush=True)
            if self.source.start():
                break
            print(f"recv {self.sinkNum}: Compressed pointcloud receiver failed to start")
            self.retry -= 1
            if self.retry <= 0:
                return
        if self.verbose:
            print(f"recv {self.sinkNum}: started")
            nStream = self.source.count()
            print(f"recv {self.sinkNum}: available streams: {nStream}")
            for i in range(nStream):
                fourcc, tilenum, quality = self.source.info_for_stream(i)
                print(f"recv {self.sinkNum}: stream {i}: 4CC={fourcc.to_bytes(4, 'big')}={fourcc}, tilenum={tilenum}, quality={quality}")
        self.receiver_loop()

    def statistics(self):
        self.print1stat('recv', self.times_recv)
        self.print1stat('decode', self.times_decode)
        self.print1stat('latency', self.times_latency)
        self.print1stat('completeloop', self.times_completeloop)
        self.print1stat('receivedsize', self.sizes_received, isInt=True)
        if self.startTime and self.stopTime and self.startTime != self.stopTime:
            bps = self.totalBytes/(self.stopTime-self.startTime)
            scale = ''
            if bps > 10000:
                bps /= 1000
                scale = 'k'
            if bps > 10000:
                bps /= 1000
                scale = 'M'
            print(f'recv {self.sinkNum}: bandwidth={bps:.0f} {scale}B/s')
        
    def print1stat(self, name, values, isInt=False):
        count = len(values)
        if count == 0:
            print(f'recv {self.sinkNum}: {name}: count=0')
            return
        minValue = min(values)
        maxValue = max(values)
        avgValue = sum(values) / count
        if isInt:
            print(f'recv {self.sinkNum}: {name}: count={count}, average={avgValue:.3f}, min={minValue:d}, max={maxValue:d}')
        else:
            print(f'recv {self.sinkNum}: {name}: count={count}, average={avgValue:.3f}, min={minValue:.3f}, max={maxValue:.3f}')

def main():
    if hasattr(signal, 'SIGQUIT'):
        signal.signal(signal.SIGQUIT, _dump_app_stacks)
    default_url = "https://vrt-evanescent.viaccess-orca.com/echo-%d/" % int(time.time())
    parser = argparse.ArgumentParser(description="Echo pointcloud streams using bin2dash, evanescent and sub")
    parser.add_argument("--url", action="store", metavar="URL", help="Base of Evanescent URL", default=default_url)
    parser.add_argument("--seg_dur", action="store", type=int, default=10000, metavar="MS", help="Bin2dash segment duration (milliseconds, default 10000)")
    parser.add_argument("--timeshift_buffer", action="store", type=int, default=30000, metavar="MS", help="Bin2dash timeshift buffer depth (milliseconds, default 30000)")
    parser.add_argument("--fps", action="store", type=float, metavar="FPS", help="Limit capture to at most FPS frames per second")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic pointclouds (watermelons) in stead of realsense")
    parser.add_argument("--tile", action="store_true", help="Encode and transmit individual tiles in stead of single pointcloud stream")
    parser.add_argument("--voxelsize", action="store", type=float, default=0, metavar="M", help="Before tiling voxelate pointcloud with size MxMxM (meters)")
    parser.add_argument("--octree_bits", action="append", type=int, metavar="N", help="Override encoder parameter (depth of octree)")
    parser.add_argument("--jpeg_quality", action="store", type=int, metavar="N", help="Override encoder parameter (jpeg quality)")
    parser.add_argument("--delay", action="store", type=int, default=1, metavar="SECS", help="Wait SECS seconds before starting receiver")
    parser.add_argument("--retry", action="store", type=int, metavar="COUNT", help="Retry COUNT times when opening the receiver fails", default=0)
    parser.add_argument("--count", type=int, action="store", metavar="N", help="Stop after receiving N pointclouds")
    parser.add_argument("--display", action="store_true", help="Display each pointcloud after it has been received")
    parser.add_argument("--savecwicpc", action="store", metavar="DIR", help="Save compressed pointclouds to DIR")
    parser.add_argument("--parallel", type=int, action="store", metavar="COUNT", help="Run COUNT parallel receivers", default=1)
    parser.add_argument("--verbose", action="store_true", help="Print information about each pointcloud after it has been received")
    args = parser.parse_args()
    #
    # Some sanity checks on the arguments
    #
    if not args.delay and not args.retry:
        print("* Warning: specifying neither --delay nor --retry will probably cause receiver to fail to start", file=sys.stderr)
    if not args.retry and args.delay * 1000 <= args.seg_dur:
        print("* Warning: --delay smaller than --seg_dur will probably cause receiver to fail to start", file=sys.stderr)
    if args.delay * 1000 >= args.timeshift_buffer:
        print("* Warning: --delay greater than --timeshift_buffer may cause segments to already be deleted before receiver picks them up", file=sys.stderr)
    if args.timeshift_buffer <= 2*args.seg_dur:
        print("* Warning: --timeshift_buffer should be more than two times --seg_dur or deletion of segments may overrun the receiver", file=sys.stderr)
    if args.timeshift_buffer < 8000:
        print("* Warning: Small values of --timeshift_buffer may cause deletion of segments to overrun the receiver", file=sys.stderr)
    #
    # Create source
    #
    b2dUrl = args.url
    subUrl = args.url + "bin2dashSink.mpd"
    print(f"command line: {' '.join(sys.argv)}")
    print(f"url: {subUrl}")
    #
    # Find all combinations of octree_bits and jpeg_quality and create encoder_params
    #
    encparamlist = []
    octree_bits_list = args.octree_bits
    jpeg_quality_list = args.jpeg_quality
    voxelsize = args.voxelsize
    if not octree_bits_list: octree_bits_list = [9]
    if not jpeg_quality_list: jpeg_quality_list = [85]
    for octree_bits in octree_bits_list:
        for jpeg_quality in jpeg_quality_list:
            encparams = cwipc.codec.cwipc_encoder_params(False, 1, 1.0, octree_bits, jpeg_quality, 16, 0, voxelsize)
            encparamlist.append(encparams)        
    b2dparams = {}
    if args.seg_dur:
        b2dparams['seg_dur_in_ms'] = args.seg_dur
    if args.timeshift_buffer:
        b2dparams['timeshift_buffer_depth_in_ms'] = args.timeshift_buffer
    sourceServer = SourceServer(args.url, fps=args.fps, synthetic=args.synthetic, tile=args.tile, encparamlist=encparamlist, b2dparams=b2dparams, verbose=args.verbose)
    sourceThread = threading.Thread(target=sourceServer.run, args=())
    if args.display:
        visualizer = Visualizer(args.verbose)
    else:
        visualizer = None
    thisVisualizer = visualizer
    #
    # Create sinks
    #
    clts = []
    threads = []
    for i in range(args.parallel):
        clt = SinkClient(subUrl, args.count, args.delay, args.retry, thisVisualizer, args.savecwicpc, args.verbose)
        thread = threading.Thread(target=clt.run, args=())
        clts.append(clt)
        threads.append(thread)
        if thisVisualizer:
            thisVisualizer.set_producer(thread)
        thisVisualizer = None
    
    #
    # Run everything
    #
    try:
        sourceThread.start()
        for thread in threads:
            thread.start()

        if visualizer:
            visualizer.run()
            
        for thread in threads:
            thread.join()
        sourceServer.stop()
        sourceThread.join()
    except KeyboardInterrupt:
        print("Interrupted.")
    except:
        traceback.print_exc()
    
    #
    # It is safe to call join (or stop) multiple times, so we ensure to cleanup
    #
    sourceServer.stop()
    for clt in clts:
        clt.stop()
    sourceThread.join()
    for thread in threads:
        thread.join()
    
    sourceServer.statistics()
    for clt in clts:
        clt.statistics()
    
if __name__ == '__main__':
    main()
    
    
    
