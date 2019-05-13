import sys
import os
import open3d
import numpy as np
import cwipc
import cwipc.codec
import cwipc.util
import re
import time

VOXEL_SIZE = 0 # 3.5    # Larger numbers mean smaller output size

TILES=(0, 1, 2, 4, 8)
ALSO_LOW=True   # Set to True to also do low quality cwicpc
    
class PlyReader:
    def __init__(self):
        self.epoch = None
        
    def grab(self, filename):
        match = re.match(r'.*pointcloud-([0-9]+).ply', filename)
        timestamp = int(match.group(1))
        if self.epoch == None:
            self.epoch = timestamp
        pc = cwipc.cwipc_read(filename, timestamp-self.epoch)
        return pc
        
def draw_o3d(o3dpc):
    """Draw open3d pointcloud"""
    open3d.draw_geometries([o3dpc])
        
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
    
def write_ply_cwipc(filename, pc):
    """Write cwipc pointcloud to PLY file"""
    cwipc.cwipc_write(filename, pc)
    
def main():
    if len(sys.argv) != 4:
        print('Usage: %s grab-source-ply-dir dest-ply-dir dest-cwicpc-dir' % sys.argv[0])
        sys.exit(1)
    grab_source_dir = sys.argv[1]
    ply_dest_dir = sys.argv[2]
    cwicpc_dest_dir = sys.argv[3]
    os.mkdir(ply_dest_dir)
    os.mkdir(cwicpc_dest_dir)
    for i in TILES:
        if i == 0: continue
        os.mkdir(cwicpc_dest_dir+str(i))
    if ALSO_LOW:
        os.mkdir(cwicpc_dest_dir+'-low')
        for i in TILES:
            if i == 0: continue
            os.mkdir(cwicpc_dest_dir+str(i)+'-low')
    
    startTime = time.time()
    count = 0
    timestamp = 0
    allfiles = os.listdir(grab_source_dir)
    allfiles.sort()
    
    # Setup the encoder group and the encoders
    
    enc_group = cwipc.codec.cwipc_new_encodergroup()
    params = cwipc.codec.cwipc_encoder_params(False, 1, 1.0, 9, 85, 16, 0, 0)
    encoders = []
    encoders.append(enc_group.addencoder(params=params))
    for i in TILES:
        if i == 0: continue
        params.tilenumber = i
        encoders.append(
            enc_group.addencoder(params=params) 
        )
    if ALSO_LOW:
        params_low = cwipc.codec.cwipc_encoder_params(False, 1, 1.0, 7, 60, 16, 0, 0)
        encoders.append(enc_group.addencoder(params=params_low))
        for i in TILES:
            if i == 0: continue
            params_low.tilenumber = i
            encoders.append(
                enc_group.addencoder(params=params_low) 
            )
    reader = PlyReader()
    for filename in allfiles:
        if os.path.splitext(filename)[1] != '.ply':
            continue
        pathname = os.path.join(grab_source_dir, filename)
        print(pathname, '...')
        basename = os.path.splitext(filename)[0]
        ply_dest_pathname = os.path.join(ply_dest_dir, filename)
        
        cwicpc_dest_pathnames = []
        cwicpc_dest_pathnames.append(os.path.join(cwicpc_dest_dir, basename + '.cwicpc'))
        for i in TILES:
            if i == 0: continue
            cwicpc_dest_pathnames.append(
                os.path.join(cwicpc_dest_dir + str(i), basename + '.cwicpc')
            )
        if ALSO_LOW:
            cwicpc_dest_pathnames.append(os.path.join(cwicpc_dest_dir + '-low', basename + '.cwicpc'))
            for i in TILES:
                if i == 0: continue
                cwicpc_dest_pathnames.append(
                    os.path.join(cwicpc_dest_dir + str(i) + '-low', basename + '.cwicpc')
                )
        
        pc = reader.grab(pathname)
        timestamp = pc.timestamp()
        print('xxxjack grabbed timestamp', timestamp)

        # Save as a plyfile
        write_ply_cwipc(ply_dest_pathname, pc)
        
        # compress and save
        enc_group.feed(pc)
        for i in range(len(encoders)):
            ok = encoders[i].available(True)
            assert ok
            data = encoders[i].get_bytes()
            with open(cwicpc_dest_pathnames[i], 'wb') as ofp:
                ofp.write(data)

        pc.free()
        
        count += 1
        
    now = time.time()
    print("Converted %d pointclouds in %f seconds" % (count, now-startTime))
    
if __name__ == '__main__':
    main()
    
    
    
