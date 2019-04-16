import sys
import os
import time
import socket
import argparse
import traceback
import cwipc
import cwipc.codec
import cwipc.realsense2
    
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
        
class SourceServer:
    def __init__(self, port=4303, count=None, plydir=None, cwicpcdir=None, params=None):
        self.socket = socket.socket()
        self.socket.bind(('', port))
        self.socket.listen()
        if cwicpcdir:
            self.cpcSource = cwicpcdir_source(cwicpcdir)
            self.grabber = None
        elif plydir:
            self.grabber = cwipc_plydir_source(plydir)
        else:
            self.grabber = cwipc.realsense2.cwipc_realsense2()
        self.times_grab = []
        self.times_encode = []
        self.times_send = []
        self.count = count
        self.params = params
        
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
            s, _ = self.socket.accept()
            t0 = time.time()
            if self.grabber:
                pc = self.grab_pc()
                t1 = time.time()
                data = self.encode_pc(pc)
                t2 = time.time()
            else:
                data = self.cpcSource.get()
                t1 = t2 = time.time()
            s.sendall(data)
            s.close()
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
    parser = argparse.ArgumentParser(description="Start server to send compressed pointclouds to a cwipc_sourceserver_sink")
    parser.add_argument("--port", type=int, action="store", metavar="PORT", help="Port to connect to", default=4303)
    parser.add_argument("--count", type=int, action="store", metavar="N", help="Stop serving after N requests")
    parser.add_argument("--plydir", action="store", metavar="DIR", help="Load PLY files from DIR in stead of grabbing them from the camera")
    parser.add_argument("--cwicpcdir", action="store", metavar="DIR", help="Load cwicpc files from DIR in stead of grabbing them from the camera and compressing them")
    parser.add_argument("--octree_bits", action="store", type=int, metavar="N", help="Override encoder parameter (depth of octree)")
    parser.add_argument("--jpeg_quality", action="store", type=int, metavar="N", help="Override encoder parameter (jpeg quality)")
    args = parser.parse_args()
    params = cwipc.codec.cwipc_encoder_params(1, False, 1, 0, 7, 8, 85, 16)
    if args.octree_bits or args.jpeg_quality:
        if args.octree_bits:
            params.octree_bits = args.octree_bits
        if args.jpeg_quality:
            params.jpeg_quality = args.jpeg_quality
    srv = SourceServer(args.port, args.count, args.plydir, args.cwicpcdir, params)
    try:
        srv.serve()
    except (Exception, KeyboardInterrupt):
        traceback.print_exc(limit=-1)
    srv.statistics()
    
if __name__ == '__main__':
    main()
    
    
    
