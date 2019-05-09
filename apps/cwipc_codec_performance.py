import sys
import os
import time
import socket
import argparse
import traceback
import cwipc
import cwipc.codec
import cwipc.realsense2
import csv

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


class EvaluatorMeasurementCodec:
    def __init__(self, params):         
        self.enc = cwipc.codec.cwipc_new_encoder(**params)
        self.dec = cwipc.codec.cwipc_new_decoder()

    def __del__(self):
        self.enc.free()
        self.dec.free()
        
    def measure(self, pc):
        curstats = {}
        t0 = time.time()
        self.enc.feed(pc)
        ok = self.enc.available(True)
        assert ok
        curstats['encode_time'] = time.time() - t0
        data = self.enc.get_bytes()
        curstats['encoded_size'] = len(data)
        
        t0 = time.time()
        self.dec.feed(data)
        ok = self.dec.available(True)
        assert ok
        curstats['decode_time'] = time.time() - t0
        decpc = self.dec.get()
        
        return curstats, decpc

class EvaluatorMeasurementCodecTwice:
    def __init__(self, params):         
        self.enc1 = cwipc.codec.cwipc_new_encoder(**params)
        self.dec1 = cwipc.codec.cwipc_new_decoder()
        self.enc2 = cwipc.codec.cwipc_new_encoder(**params)
        self.dec2 = cwipc.codec.cwipc_new_decoder()

    def __del__(self):
        self.enc1.free()
        self.dec1.free()
        self.enc2.free()
        self.dec2.free()
        
    def measure(self, pc):
        curstats = {}
        
        # Encode a first time, don't measure
        self.enc1.feed(pc)
        ok = self.enc1.available(True)
        assert ok
        data = self.enc1.get_bytes()
        self.dec1.feed(data)
        ok = self.dec1.available(True)
        assert ok
        intpc = self.dec1.get()
        
        # Now do the measurement
        t0 = time.time()
        self.enc2.feed(intpc)
        ok = self.enc2.available(True)
        assert ok
        curstats['encode_time'] = time.time() - t0
        data = self.enc2.get_bytes()
        curstats['encoded_size'] = len(data)
        
        t0 = time.time()
        self.dec2.feed(data)
        ok = self.dec2.available(True)
        assert ok
        curstats['decode_time'] = time.time() - t0
        decpc = self.dec2.get()
        
        return curstats, decpc

ALL_MEASUREMENTS = {
    'codec' : EvaluatorMeasurementCodec,
    'twice' : EvaluatorMeasurementCodecTwice
}      
    
class Evaluator:
    octree_bits = [11,10,9,8,7]
    jpeg_quality = [85,60,40]
    measurement = ['codec']
    
    def __init__(self, plydir=None, count=300, octree_bits=None, jpeg_quality=None, measurement=None):
        if plydir:
            self.grabber = cwipc_plydir_source(plydir)
        else:
            self.grabber = cwipc.realsense2.cwipc_realsense2()
        if octree_bits:
            self.octree_bits = octree_bits
        if jpeg_quality:
            self.jpeg_quality = jpeg_quality
        if measurement:
            self.measurement = measurement
        self.count = count
        self.stats = []
        
    def grab_pc(self):
        pc = self.grabber.get()
        return pc

    def run(self):
        for cur_measurement in self.measurement:
            for cur_octree_bits in self.octree_bits:
                for cur_jpeg_quality in self.jpeg_quality:
                    klass = ALL_MEASUREMENTS[cur_measurement]
                    measurer = klass(params={'octree_bits':cur_octree_bits, 'jpeg_quality':cur_jpeg_quality})
                    for cur_num in range(self.count):
                        pc = self.grab_pc()
                        cur_orig_pointcount = len(pc.get_points())
                    
                        curstats, decpc = measurer.measure(pc)

                        cur_decoded_pointcount = len(decpc.get_points())
                    
                        # Compare qualities (xxxjack to be done)
                    
                        for k, v in locals().items():
                            if k[:4] == 'cur_':
                                curstats[k[4:]] = v
                        self.stats.append(curstats)
                    
                        pc.free()
                        decpc.free()
            
    def statistics(self, output=sys.stdout):
        # Determine the fieldnames in the CSV output
        fieldnames = ['measurement', 'octree_bits', 'jpeg_quality', 'num', 'orig_pointcount', 'decoded_pointcount', 'encode_time', 'decode_time', 'encoded_size']
        allkeys = set()
        for stat in self.stats:
            allkeys |= set(stat.keys())
        for k in allkeys:
            if not k in fieldnames:
                fieldnames.append(k)
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for stat in self.stats:
            writer.writerow(stat)

def main():
    parser = argparse.ArgumentParser(description="Test compression and decompression performance")
    parser.add_argument("--plydir", action="store", metavar="DIR", help="Load PLY files from DIR")
    parser.add_argument("--output", action="store", metavar="FILE", help="Save results as CSV to output file (default: stdout)")
    parser.add_argument("--measurement", action="append", metavar="NAME", help="Override type of measurements done (default: codec)")
    parser.add_argument("--octree_bits", action="append", type=int, metavar="N", help="Override encoder parameter (depth of octree)")
    parser.add_argument("--jpeg_quality", action="append", type=int, metavar="N", help="Override encoder parameter (jpeg quality)")
    parser.add_argument("--count", type=int, action="store", metavar="N", help="Number of pointclouds to compress for each combination")
    args = parser.parse_args()
    srv = Evaluator(args.plydir, args.count, args.octree_bits, args.jpeg_quality, args.measurement)
    try:
        srv.run()
    except (Exception, KeyboardInterrupt):
        traceback.print_exc()
    if args.output:
        with open(args.output, 'w') as fp:
            srv.statistics(fp)
    else:
        srv.statistics()

if __name__ == '__main__':
    main()
    
    
    