import sys
import os
import time
import socket
import argparse
import traceback
import subprocess
import cwipc
import cwipc.codec
import cwipc.realsense2

# Convoluted code warning: adding ../python directory to path so we can import subsource
_sourcedir = os.path.dirname(__file__)
_pardir = os.path.dirname(_sourcedir)
_pythondir = os.path.join(_pardir, 'python')
sys.path.append(_pythondir)

from bin2dash import CpcBin2dashSink
    
class cwipc_plydir_source:
    def __init__(self, dirname):
        self.dirname = dirname
        self._loadfilenames()
        
    def _loadfilenames(self):
        filenames = os.listdir(self.dirname)
        filenames = list(filter(lambda fn: fn[-4:] == '.ply', filenames))
        filenames = sorted(filenames, reverse=True)
        self.filenames = list(map(lambda fn: os.path.join(self.dirname, fn), filenames))
        
    def _nextfilename(self):
        assert self.filenames
        rv = self.filenames.pop()
        if len(self.filenames) == 0:
            self._loadfilenames()
        return rv
            
    def eof(self):
        return len(self.filenames) == 0
        
    def available(self, wait):
        return True
        
    def get(self):
        fn = self._nextfilename()
        pc = cwipc.cwipc_read(fn, int(time.time()*1000))
        return pc
        
    def free(self):
        self.filenames = []
        
class cwicpcdir_source:
    def __init__(self, dirname):
        self.dirname = dirname
        self._loadfilenames()
        
    def _loadfilenames(self):
        filenames = os.listdir(self.dirname)
        filenames = list(filter(lambda fn: fn[-7:] == '.cwicpc', filenames))
        filenames = sorted(filenames, reverse=True)
        self.filenames = list(map(lambda fn: os.path.join(self.dirname, fn), filenames))
        
    def _nextfilename(self):
        assert self.filenames
        rv = self.filenames.pop()
        if len(self.filenames) == 0:
            self._loadfilenames()
        return rv
            
    def eof(self):
        return len(self.filenames) == 0
        
    def available(self, wait):
        return True
        
    def get(self):
        fn = self._nextfilename()
        cpc = open(fn, 'rb').read()
        return cpc
        
    def free(self):
        self.filenames = []
        
class SourceServerSink:
    def __init__(self):
        pass
        
    def feed(self, cpc):
        pass
        
    def canfeed(self, timestamp, wait=True):
        return True
        
class SourceServerNetworkSink(SourceServerSink):
    def __init__(self, port):
        self.socket = socket.socket()
        self.socket.bind(('', port))
        self.socket.listen()
        self.curSocket = None
        
    def __del__(self):
        print('xxxjack __del__ SourceServerNetworkSink')
        if self.socket:
            self.socket.close()
            self.socket = None
        if self.curSocket:
            self.curSocket.close()
            self.curSocket = None
            
    def feed(self, cpc):
        self.curSocket.sendall(cpc)
        self.curSocket.close()
        self.curSocket = None
        
    def canfeed(self, timestamp, wait=True):
        assert wait
        self.curSocket, _ = self.socket.accept()


class SourceServer:
    def __init__(self, nosend=False, port=4303, bin2dash=None, count=None, plydir=None, cwicpcdir=None, params=None):
        self.grabber = None
        if nosend:
            self.sink = SourceServerSink()
        elif bin2dash != None:
            self.sink = CpcBin2dashSink(bin2dash)
        else:
            self.sink = SourceServerNetworkSink(port)
        if cwicpcdir:
            self.cpcSource = cwicpcdir_source(cwicpcdir)
        elif plydir:
            self.grabber = cwipc_plydir_source(plydir)
        else:
            self.grabber = cwipc.realsense2.cwipc_realsense2()
        self.times_grab = []
        self.times_encode = []
        self.sizes_encode = []
        self.times_send = []
        self.count = count
        self.params = params
        
    def __del__(self):
        if self.grabber:
            self.grabber.free()
        self.grabber = None

    def grab_pc(self):
        pc = self.grabber.get()
        return pc

    def encode_pc(self, pc):
        enc = cwipc.codec.cwipc_new_encoder(params=self.params)
        enc.feed(pc)
        gotData = enc.available(True)
        assert gotData
        data = enc.get_bytes()
        pc.free()
        enc.free()
        return data
        
    def serve(self):
        while True:
            self.sink.canfeed(time.time(), wait=True)
            t0 = time.time()
            if self.grabber:
                pc = self.grab_pc()
                t1 = time.time()
                data = self.encode_pc(pc)
                t2 = time.time()
            else:
                data = self.cpcSource.get()
                t1 = t2 = time.time()
            self.sizes_encode.append(len(data))
            self.sink.feed(data)
            t3 = time.time()
            self.times_grab.append(t1-t0)
            self.times_encode.append(t2-t1)
            self.times_send.append(t3-t2)
            if self.count != None:
                self.count -= 1
                if self.count <= 0:
                    break
            
    def statistics(self):
        self.print1stat('grab', self.times_grab)
        self.print1stat('encode', self.times_encode)
        self.print1stat('send', self.times_send)
        self.print1stat('encodedsize', self.sizes_encode, isInt=True)
        
    def print1stat(self, name, values, isInt=False):
        count = len(values)
        if count == 0:
            print('{}: count=0'.format(name))
            return
        minValue = min(values)
        maxValue = max(values)
        avgValue = sum(values) / count
        if isInt:
            fmtstring = '{}: count={}, average={:.3f}, min={:d}, max={:d}'
        else:
            fmtstring = '{}: count={}, average={:.3f}, min={:.3f}, max={:.3f}'
        print(fmtstring.format(name, count, avgValue, minValue, maxValue))
            
def main():
    parser = argparse.ArgumentParser(description="Start server to send compressed pointclouds to a cwipc_sourceserver_sink")
    parser.add_argument("--nosend", action="store_true", help="Do not send compressed data anywhere, only grab and collect statistics")
    parser.add_argument("--bin2dash", action="store", metavar="URL", help="Send compressed data to bin2dash URL, empty string for storing in local files")
    parser.add_argument("--gpacdash", action="store_true", help="Start (and stop) gpac-dash.js, use in conjunction with --bin2dash to serve from local files")
    parser.add_argument("--port", type=int, action="store", metavar="PORT", help="Port to connect to", default=4303)
    parser.add_argument("--count", type=int, action="store", metavar="N", help="Stop serving after N requests")
    parser.add_argument("--plydir", action="store", metavar="DIR", help="Load PLY files from DIR in stead of grabbing them from the camera")
    parser.add_argument("--cwicpcdir", action="store", metavar="DIR", help="Load cwicpc files from DIR in stead of grabbing them from the camera and compressing them")
    parser.add_argument("--octree_bits", action="store", type=int, metavar="N", help="Override encoder parameter (depth of octree)")
    parser.add_argument("--jpeg_quality", action="store", type=int, metavar="N", help="Override encoder parameter (jpeg quality)")
    args = parser.parse_args()
    params = cwipc.codec.cwipc_encoder_params(False, 1, 1.0, 9, 85, 16, 0, 0)
    if args.octree_bits or args.jpeg_quality:
        if args.octree_bits:
            params.octree_bits = args.octree_bits
        if args.jpeg_quality:
            params.jpeg_quality = args.jpeg_quality
    srv = SourceServer(args.nosend, args.port, args.bin2dash, args.count, args.plydir, args.cwicpcdir, params)
    dashServer = None
    if args.gpacdash:
        _topdir = os.path.dirname(_pardir)
        gpacPath = os.path.join(_topdir, 'node-gpac-dash', 'gpac-dash.js')
        if not os.path.exists(gpacPath):
            print('%s: No gpacdash at %s' % (sys.argv[0], gpacPath), file=sys.stderr)
            sys.exit(1)
        dashServer = subprocess.Popen(["node", gpacPath])
    try:
        srv.serve()
    except (Exception, KeyboardInterrupt):
        traceback.print_exc()
    if dashServer:
        dashServer.terminate()
    srv.statistics()
    
if __name__ == '__main__':
    main()
    
    
    
