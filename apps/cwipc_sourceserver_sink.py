import sys
import os
import time
import socket
import argparse
import traceback
import open3d
import numpy as np
import cwipc
import cwipc.codec
from subsource import CpcSubSource
    
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
    def __init__(self, hostname='localhost', port=4303, count=None, display=False, sub=None, savedir=None):
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
        print('xxxjack cpc', cpc)
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
        self.visualiser.create_window()

    def draw_o3d(self, o3dpc):
        """Draw open3d pointcloud"""
        if self.visualiser_o3dpc == None:
            self.visualiser_o3dpc = o3dpc
            self.visualiser.add_geometry(o3dpc)
        else:
            self.visualiser_o3dpc.points = o3dpc.points
            self.visualiser_o3dpc.colors = o3dpc.colors
        print(len(self.visualiser_o3dpc.points), 'points')
        self.visualiser.update_geometry()
        self.visualiser.update_renderer()
        self.visualiser.poll_events()
        
    def stop_o3d(self):
        self.visualiser.destroy_window()

    def run(self):
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
    parser.add_argument("--sub", action="store", metavar="URL", help="Don't use direct socket connection but use Signals-Unity-Bridge connection to URL")
    parser.add_argument("--count", type=int, action="store", metavar="N", help="Stop receiving after N requests")
    parser.add_argument("--display", action="store_true", help="Display each pointcloud after it has been received")
    parser.add_argument("--savecwicpc", action="store", metavar="DIR", help="Save compressed pointclouds to DIR")
    args = parser.parse_args()
    clt = SinkClient(args.hostname, args.port, args.count, args.display, args.sub, args.savecwicpc)
    try:
        clt.run()
    except (Exception, KeyboardInterrupt):
        traceback.print_exc(limit=-1)
    clt.statistics()
    
if __name__ == '__main__':
    main()
    
    
    
