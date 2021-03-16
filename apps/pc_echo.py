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
try:
    import cwipc.realsense2 as realsense2
except ModuleNotFoundError:
    realsense2 = None
    
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
                pc = self.queue.get(timeout=1)
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
        ok = self.visualiser.feed(pc, True)
        pc.free()
        if not ok: 
            print('display: window.feed() returned False')
            return False
        if self.visualiser.interact(None, "q", 30) == "q":
            return False
        return True

class SourceServer:
    def __init__(self, bin2dash, *, fps=None, synthetic=False, tile=False, encparamlist=[], b2dparams={}, verbose=False):
        self.verbose = verbose
        self.fps = fps
        self.times_grab = []
        self.pointcounts_grab = []
        self.stopped = False
        self.lastGrabTime = None
        self.threads = []
        self.encoders = []
        self.transmitters = []
        self.encodergroup = None
        self.transmittergroup = None
                
        if synthetic:
            self.grabber = cwipc.cwipc_synthetic()
        elif realsense2:
            self.grabber = realsense2.cwipc_realsense2()
        else:
            print(f"grab: No realsense support, using synthetic")
            self.grabber = cwipc.cwipc_synthetic()
        
        if tile:
            self.tiles = []
            maxTile = self.grabber.maxtile()
            if self.verbose: print(f"grab: {maxTile} tiles")
            for i in range(maxTile):
                tileInfo = self.grabber.get_tileinfo_dict(i)
                if self.verbose: print(f"grab: tile {i}: {tileInfo}")
            #self.tiles = range(0, maxTile)
            self.tiles = range(1, maxTile)
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
        del self.transmittergroup        
        del self.grabber
        del self.encodergroup
        del self.transmitters
        del self.threads
        del self.encoders

    def stop(self):
        if self.stopped: return
        if self.verbose: print("grab: stopping", flush=True)
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
            self.pointcounts_grab.append(pc.count())
            sourceTime = pc.timestamp()
            t1 = time.time()
            self.encodergroup.feed(pc)
            pc.free()
            self.times_grab.append(t1-t0)
        if self.verbose: print('grab: stopped', flush=True)
            
    def statistics(self):
        self.print1stat('capture_duration', self.times_grab)
        self.print1stat('capture_pointcount', self.pointcounts_grab, isInt=True)
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
        if self.stopped: return
        if self.verbose: print(f"send {self.xmitNum}: stopping", flush=True)
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
        self.print1stat('encode_duration', self.times_encode)
        self.print1stat('send_bytecount', self.sizes_encode, isInt=True)
        self.print1stat('send_duration', self.times_send)
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

class Receiver:
    def __init__(self, sub, sinkNum, streamNum, count=None, pcsink=None, savedir=None, verbose=False):
        self.sub = sub
        self.sinkNum = sinkNum
        self.streamNum = streamNum
        self.count = count
        self.pcsink = pcsink
        self.verbose = verbose
        self.times_recv = []
        self.times_decode = []
        self.pointcounts_decode = []
        self.times_latency = []
        self.times_completeloop = []
        self.sizes_received = []
        self.savedir = savedir
        self.stopped = False
        self.startTime = None
        self.stopTime = None
        self.totalBytes = 0

    def stop(self):
        if self.stopped: return
        if self.verbose: print(f"recv {self.sinkNum}.{self.streamNum}: stopping", flush=True)
        self.stopped = True

    def run(self):
        seqno = 1
        while not self.stopped:
            t0 = time.time()
            if self.startTime == None: self.startTime = time.time()
            cpc = self.sub.read_cpc(self.streamNum)
            self.stopTime = time.time()
            if not cpc:
                if self.verbose: print(f"recv {self.sinkNum}.{self.streamNum}: read_cpc() returned None", flush=True)
                break
            self.sizes_received.append(len(cpc))
            self.totalBytes += len(cpc)
            t1 = time.time()
            pc = self.decompress(cpc)
            if not pc:
                print(f"recv {self.sinkNum}.{self.streamNum}: decompress({len(cpc)} bytes of compressed data) failed to produce a pointcloud")
            t2 = time.time()
            self.times_recv.append(t1-t0)
            self.times_decode.append(t2-t1)
            self.pointcounts_decode.append(pc.count())
            sinkTime = time.time()
            if pc:
                sourceTime = pc.timestamp() / 1000.0
                if self.verbose: print(f"recv {self.sinkNum}.{self.streamNum}: {t1}: compressed size: {len(cpc)}, timestamp: {sourceTime}, waited: {t1-t0}, latency: {sinkTime-sourceTime}", flush=True)
                self.times_latency.append(sinkTime-sourceTime)
            if cpc and self.savedir:
                savefile = 'pointcloud-%d-%05d.cwicpc' % (self.streamNum, seqno)
                seqno += 1
                with open(os.path.join(self.savedir, savefile), 'wb') as fp:
                    fp.write(cpc)
            if pc and self.pcsink:
                self.pcsink.feed(pc)
            else:
                pc.free()
            if self.count != None:
                self.count -= 1
                if self.count <= 0:
                    if self.verbose: print(f"recv {self.sinkNum}.{self.streamNum}: requested --count reached", flush=True)
                    break
            t3 = time.time()
            self.times_completeloop.append(t3-t0)
        if self.verbose: print(f"recv {self.sinkNum}.{self.streamNum}: stopped", flush=True)
        
                     
    def decompress(self, cpc):
        decomp = cwipc.codec.cwipc_new_decoder()
        decomp.feed(cpc)
        gotData = decomp.available(True)
        if not gotData: return None
        pc = decomp.get()
        return pc
   
    def statistics(self):
        self.print1stat('recv_duration', self.times_recv)
        self.print1stat('recv_bytecount', self.sizes_received, isInt=True)
        self.print1stat('recv_loop_duration', self.times_completeloop)
        self.print1stat('decode_duration', self.times_decode)
        self.print1stat('decode_pointcount', self.pointcounts_decode, isInt=True)
        self.print1stat('end_to_end_latency', self.times_latency)
        if self.startTime and self.stopTime and self.startTime != self.stopTime:
            bps = self.totalBytes/(self.stopTime-self.startTime)
            scale = ''
            if bps > 10000:
                bps /= 1000
                scale = 'k'
            if bps > 10000:
                bps /= 1000
                scale = 'M'
            print(f'recv {self.sinkNum}.{self.streamNum}: bandwidth={bps:.0f} {scale}B/s')
        
    def print1stat(self, name, values, isInt=False):
        count = len(values)
        if count == 0:
            print(f'recv {self.sinkNum}.{self.streamNum}: {name}: count=0')
            return
        minValue = min(values)
        maxValue = max(values)
        avgValue = sum(values) / count
        if isInt:
            print(f'recv {self.sinkNum}.{self.streamNum}: {name}: count={count}, average={avgValue:.3f}, min={minValue:d}, max={maxValue:d}')
        else:
            print(f'recv {self.sinkNum}.{self.streamNum}: {name}: count={count}, average={avgValue:.3f}, min={minValue:.3f}, max={maxValue:.3f}')

class SinkClient:
    SINKNUM = 1
    
    def __init__(self, subUrl, count=None, delay=0, retry=0, pcsink=None, savedir=None, recvq=None, verbose=False):
        self.sinkNum = SinkClient.SINKNUM
        SinkClient.SINKNUM += 1
        self.subUrl = subUrl
        self.verbose = verbose
        self.count = count
        self.delay = delay
        self.retry = retry
        self.pcsink = pcsink
        self.savedir = savedir
        self.wantedQuality = recvq
        if self.wantedQuality == None:
            self.wantedQuality = 'first'
        self.stopped = False
        self.tile2info = {}
        self.receivers = []
        self.threads = []
        if verbose: print(f"sink {self.sinkNum}: sub url={subUrl}", flush=True)
        self.sub = None

    def stop(self):
        if self.stopped: return
        if self.verbose: print(f"sink {self.sinkNum}: stopping", flush=True)
        self.stopped = True
        for r in self.receivers:
            r.stop()
        for t in self.threads:
            t.join()
        
    def run(self):
        while True:
            if self.delay:
                time.sleep(self.delay)
                if self.verbose: print(f"recv {self.sinkNum}: starting", flush=True)
            sub = CpcSubSource(self.subUrl)
            if sub.start():
                self.sub = sub
                break
            print(f"recv {self.sinkNum}: Compressed pointcloud receiver failed to start", flush=True)
            self.retry -= 1
            if self.retry <= 0:
                return
        if self.verbose:
            print(f"recv {self.sinkNum}: started", flush=True)
        nStream = self.sub.count()
        if self.verbose:
            print(f"recv {self.sinkNum}: available streams: {nStream}", flush=True)
        #
        # Iterate over the streams and collect all available tilenumbers, stream numbers and qualities
        #
        for i in range(nStream):
            fourcc, tilenum, quality = self.sub.cpc_info_for_stream(i)
            if self.verbose:
                print(f"recv {self.sinkNum}: stream {i}: 4CC={fourcc.to_bytes(4, 'big')}={fourcc}, tilenum={tilenum}, quality={quality}", flush=True)
            infoList = self.tile2info.get(tilenum, [])
            infoList.append((i, quality))
            self.tile2info[tilenum] = infoList
        #
        # Start one receiver per tilenumber
        #
        tileNumbers = list(self.tile2info.keys())
        tileNumbers.sort()
        for tileNum in tileNumbers:
            print(f"recv {self.sinkNum}: tile {tileNum}:", end='')
            for sn, q in self.tile2info[tileNum]:
                print(f" quality={q}:streamNum={sn}", end='')
            print('', flush=True)
        selected = None
        for tileNum in tileNumbers:
            tileInfo = self.tile2info[tileNum]
            if self.wantedQuality == 'first' or self.wantedQuality == 'default':
                selected = tileInfo[0]
            elif self.wantedQuality == 'last':
                selected = tileInfo[-1]
            elif self.wantedQuality == 'lowest':
                selected = tileInfo[0]
                for ti in tileInfo[1:]:
                    sn, q = ti
                    if q < selected[1]:
                        selected = ti
            elif self.wantedQuality == 'highest':
                selected = tileInfo[0]
                for ti in tileInfo[1:]:
                    sn, q = ti
                    if q > selected[1]:
                        selected = ti
            else:
                selected = None
                for ti in tileInfo:
                    sn, q = ti
                    if q == int(self.wantedQuality):
                        selected = ti
                if not selected:
                    print(f"recv{self.sinkNum}: tile {tileNum}: quality {self.wantedQuality} not available. Skipping tile.")
                    self.sub.disable_stream(tileNum)
                    continue
            streamNum, quality = selected
            if self.wantedQuality == 'default':
                # We don't use enable_stream, we just assume that the default stream
                # (the first one for this tile) has already been enabled automatically by the
                # sub.
                self.sub.enable_stream(tileNum, quality)
            print(f"recv{self.sinkNum}: tile {tilenum}: selected stream {streamNum}, quality {quality}")
            receiver = Receiver(self.sub, self.sinkNum, streamNum, self.count, self.pcsink, self.savedir, self.verbose)
            thr = threading.Thread(target=receiver.run, args=())
            self.receivers.append(receiver)
            self.threads.append(thr)
        if self.verbose:
            print(f"recv {self.sinkNum}: starting receivers", flush=True)
        for t in self.threads:
            t.start()
        if self.verbose:
            print(f"recv {self.sinkNum}: waiting for receivers", flush=True)
        for t in self.threads:
            t.join()
        if self.verbose:
            print(f"recv {self.sinkNum}: receivers done", flush=True)

    def statistics(self):
        for r in self.receivers:
            r.statistics()
        
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
    parser.add_argument("--octree_bits", action="append", type=int, metavar="N", help="Override encoder parameter (depth of octree). Can be specified multiple times.")
    parser.add_argument("--jpeg_quality", action="store", type=int, metavar="N", help="Override encoder parameter (jpeg quality). Can be specified multiple times.")
    parser.add_argument("--delay", action="store", type=int, default=1, metavar="SECS", help="Wait SECS seconds before starting receiver")
    parser.add_argument("--retry", action="store", type=int, metavar="COUNT", help="Retry COUNT times when opening the receiver fails. Sets --delay to 1 if not set.", default=0)
    parser.add_argument("--count", type=int, action="store", metavar="N", help="Stop after receiving N pointclouds")
    parser.add_argument("--recvq", type=str, metavar="Q", help="Receive each tile in quality Q. Special values: default, first, last, lowest, highest", default="default")
    parser.add_argument("--display", action="store_true", help="Display each pointcloud after it has been received")
    parser.add_argument("--savecwicpc", action="store", metavar="DIR", help="Save compressed pointclouds to DIR")
    parser.add_argument("--parallel", type=int, action="store", metavar="COUNT", help="Run COUNT parallel receivers", default=1)
    parser.add_argument("--verbose", action="store_true", help="Print information about each pointcloud after it has been received")
    args = parser.parse_args()
    if args.retry and not args.delay:
        args.delay = 1
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
        clt = SinkClient(subUrl, args.count, args.delay, args.retry, thisVisualizer, args.savecwicpc, args.recvq, args.verbose)
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
            for clt in clts:
                clt.stop()
            sourceServer.stop()
            
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
    
    
    
