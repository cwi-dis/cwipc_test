import sys
import os
import time
import socket
import argparse
import traceback
import cwipc
import cwipc.codec
import threading

# Convoluted code warning: adding ../python directory to path so we can import subsource
_sourcedir = os.path.dirname(__file__)
_sourcedir = os.path.realpath(_sourcedir)
_pardir = os.path.dirname(_sourcedir)
_pythondir = os.path.join(_pardir, 'python')
sys.path.append(_pythondir)
import subsource
try:
    subsource._signals_unity_bridge_dll()
except RuntimeError:
    pass
from subsource import CpcSubSource

# NOTE: open3d must be imported after all the DLLs have been loaded (sigh)
import numpy as np
import open3d


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
        
class CpcSocketSource:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

    def start(self):
        return True
        
    def read_cpc(self):
        with socket.socket() as s:
            try:
                s.connect((self.hostname, self.port))
            except socket.error as err:
                print('connecting to {}:{}: {}'.format(self.hostname, self.port, err))
                raise
            rv = b''
            while True:
                data = s.recv(8192)
                if not data: break
                rv += data
            return rv
        
class SinkClient:
    def __init__(self, hostname='localhost', port=4303, count=None, display=False, sub=None, savedir=None, verbose=False):
        if sub:
            self.source = CpcSubSource(sub)
        else:
            self.source = CpcSocketSource(hostname, port)
        self.count = count
        self.display = display
        self.times_recv = []
        self.times_decode = []
        self.times_latency = []
        self.times_completeloop = []
        self.visualiser = None
        self.visualiser_o3dpc = None
        self.savedir = savedir
        self.verbose = verbose

    def receiver_loop(self):
        seqno = 1
        while True:
            t0 = time.time()
            cpc = self.source.read_cpc()
            if not cpc: break
            t1 = time.time()
            pc = self.decompress(cpc)
            t2 = time.time()
            self.times_recv.append(t1-t0)
            self.times_decode.append(t2-t1)
            sinkTime = time.time()
            if pc:
                sourceTime = pc.timestamp() / 1000.0
                if self.verbose: print("%f: compressed size: %d, timestamp: %f, waited: %f, latency: %f" % (t1, len(cpc), sourceTime, t1-t0, sinkTime-sourceTime), flush=True)
                self.times_latency.append(sinkTime-sourceTime)
            if cpc and self.savedir:
                savefile = 'pointcloud-%05d.cwicpc' % seqno
                seqno += 1
                with open(os.path.join(self.savedir, savefile), 'wb') as fp:
                    fp.write(cpc)
            if pc and self.display:
                self.show(pc)
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
        
    def show(self, pc):
        o3dpc = cwipc_to_o3d(pc)
        self.draw_o3d(o3dpc)
            
    def start_o3d(self):
        self.visualiser = open3d.Visualizer()
        self.visualiser.create_window(width=960, height=540)

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

    def run(self):
        if not self.source.start():
            print("Compressed pointcloud source failed to start")
            return
        if self.display:
            self.start_o3d()
        try:
            self.receiver_loop()
        finally:
            if self.display:
                self.stop_o3d()

    def statistics(self):
        self.print1stat('recv', self.times_recv)
        self.print1stat('decode', self.times_decode)
        self.print1stat('latency', self.times_latency)
        self.print1stat('completeloop', self.times_completeloop)
        
    def print1stat(self, name, values):
        count = len(values)
        if count == 0:
            print('{}: count=0'.format(name))
            return
        minValue = min(values)
        maxValue = max(values)
        avgValue = sum(values) / count
        print('{}: count={}, average={:.3f}, min={:.3f}, max={:.3f}'.format(name, count, avgValue, minValue, maxValue))

def main():
    parser = argparse.ArgumentParser(description="Receive compressed pointclouds from a cwipc_sourceserver_source and optionally display them")
    parser.add_argument("--hostname", action="store", metavar="HOSTNAME", help="Host or IP address to connect to", default="localhost")
    parser.add_argument("--port", type=int, action="store", metavar="PORT", help="Port to connect to", default=4303)
    parser.add_argument("--sub", action="store", metavar="URL", help="Don't use direct socket connection but use Signals-Unity-Bridge connection to URL. Example URL:  https://vrt-evanescent.viaccess-orca.com/pctest/bin2dashSink.mpd")
    parser.add_argument("--count", type=int, action="store", metavar="N", help="Stop receiving after N requests")
    parser.add_argument("--display", action="store_true", help="Display each pointcloud after it has been received")
    parser.add_argument("--savecwicpc", action="store", metavar="DIR", help="Save compressed pointclouds to DIR")
    parser.add_argument("--verbose", action="store_true", help="Print information about each pointcloud after it has been received")
    parser.add_argument("--parallel", type=int, action="store", metavar="COUNT", help="Run COUNT parallel sessions", default=0)
    
    args = parser.parse_args()
    if args.parallel == 0:
        clt = SinkClient(args.hostname, args.port, args.count, args.display, args.sub, args.savecwicpc, args.verbose)
        try:
            clt.run()
        except (Exception, KeyboardInterrupt):
            traceback.print_exc()
        clt.statistics()
    else:
        clts = []
        for i in range(args.parallel):
            clt = SinkClient(args.hostname, args.port, args.count, args.display, args.sub, args.savecwicpc, args.verbose)
            clts.append(clt)
        threads = []
        for clt in clts:
            threads.append(threading.Thread(target=clt.run, args=()))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for clt in clts:
            clt.statistics()
    
if __name__ == '__main__':
    main()
    
    
    