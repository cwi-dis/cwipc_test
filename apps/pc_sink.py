import sys
import os
import time
import socket
import argparse
import traceback
import cwipc
import cwipc.codec
#from cwipc.scripts._scriptsupport import *
from cwipc.scripts.cwipc_view import Visualizer
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
    def __init__(self, hostname='localhost', port=4303, count=None, visualizer=None, sub=None, savedir=None, verbose=False):
        if sub:
            self.source = CpcSubSource(sub)
        else:
            self.source = CpcSocketSource(hostname, port)
        self.count = count
        self.visualizer = visualizer
        self.visualizer_thread = None
        self.times_recv = []
        self.times_decode = []
        self.times_latency = []
        self.times_completeloop = []
        self.savedir = savedir
        self.verbose = verbose
        self.stopped = False
        if self.visualizer:
            self.visualizer.set_producer(self)
        
    def is_alive(self):
        return not self.stopped
        
    def receiver_loop(self):
        seqno = 1
        while True:
            if self.visualizer and not self.visualizer.is_alive():
                break
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
            if pc:
                if self.visualizer:
                    self.visualizer.feed(pc)
                else:
                    pc.free()
            if self.count != None:
                self.count -= 1
                if self.count <= 0:
                    break
            t3 = time.time()
            self.times_completeloop.append(t3-t0)
        self.stopped = True
            
    def decompress(self, cpc):
        decomp = cwipc.codec.cwipc_new_decoder()
        decomp.feed(cpc)
        gotData = decomp.available(True)
        if not gotData: return None
        pc = decomp.get()
        return pc
        
    def run(self):
        if not self.source.start():
            print("Compressed pointcloud source failed to start")
            return
        try:
            if self.visualizer:
                my_thread = threading.Thread(target=self.receiver_loop, args=())
                my_thread.start()
                self.visualizer.run()
                my_thread.join()
            else:
                self.receiver_loop()
        finally:
            self.stopped = True

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
    visualizer = None
    visualizer_thread = None
    if args.display:
        visualizer = Visualizer(verbose=args.verbose)
    if args.parallel == 0:
        clt = SinkClient(args.hostname, args.port, args.count, visualizer, args.sub, args.savecwicpc, args.verbose)
        try:
            clt.run()
        except (Exception, KeyboardInterrupt):
            traceback.print_exc()
        clt.statistics()
    else:
        clts = []
        for i in range(args.parallel):
            clt = SinkClient(args.hostname, args.port, args.count, visualizer, args.sub, args.savecwicpc, args.verbose)
            clts.append(clt)
            visualizer = None
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
    
    
    
