import sys
import os
import open3d
import numpy as np
import cwipc
import cwipc.codec
import cwipc.util
import time

VOXEL_SIZE = 2.5    # Larger numbers mean smaller output size
SCALE_FACTOR = 500  # Conversion factor from loot xyz values to our xyz values
TRANSLATE_X = -0.35 # Conversion (after scaling) of X values
TRANSLATE_Y = 0     # Conversion (after scaling) of Y values
TRANSLATE_Z = -0.35 # Conversion (after scaling) of Z values
TIME_INCREMENT = 33 # Increment in timestamp between successive pointclouds
O3D_BROKEN = True

MAXTILES=4  # Number of tiles (in addition to tile 0) to encode
ALSO_LOW=True   # Set to True to also do low quality cwicpc

def read_loot_ply_o3d(filename):
    """Read PLY file using open3d, scale it and downsample it. Returns open3d pointcloud"""
    if O3D_BROKEN:
        pc = cwipc.cwipc_read(filename, 0)
        original = cwipc_to_o3d(pc)
        pc.free()
        del pc
    else:
        original = open3d.io.read_point_cloud(filename)
    downsampled = open3d.geometry.PointCloud.voxel_down_sample(original, voxel_size=VOXEL_SIZE)
    points = np.asarray(downsampled.points)
    translate = np.array([TRANSLATE_X, TRANSLATE_Y, TRANSLATE_Z])
    points /= SCALE_FACTOR
    points += translate
    return downsampled
    
def write_ply_o3d(filename, o3dpc):
    """Write PLY file from open3d pointcloud"""
    open3d.io.write_point_cloud(filename, o3dpc, write_ascii=True)
    
def draw_o3d(o3dpc):
    """Draw open3d pointcloud"""
    open3d.visualization.draw_geometries([o3dpc])
    
def o3d_to_cwipc(o3dpc, timestamp):
    """Convert open3d pointcloud to cwipc pointcloud"""
    # Note that this method is inefficient, it can probably be done
    # in-place with some numpy magic
    points = list(o3dpc.points)
    colors = list(o3dpc.colors)
    rv = []
    pointsandcolors = zip(points, colors)
    for (x, y, z), (r, g, b) in pointsandcolors:
        if MAXTILES > 0:
            if MAXTILES == 2:
                side = 1 if x < 0 else 2
            elif MAXTILES == 4:
                if x < 0 and z < 0:
                    side = 1
                elif x < 0 and z >= 0:
                    side = 2
                elif x >= 0 and z < 0:
                    side = 3
                else:
                    side = 4
        r = int(r*255)
        g = int(g*255)
        b = int(b*255)
        rv.append((x, y, z, r, g, b, side))
    return cwipc.cwipc_from_points(rv, timestamp)
    
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
    points_v = open3d.utility.Vector3dVector(points)
    colors_v = open3d.utility.Vector3dVector(colors)
    rv = open3d.geometry.PointCloud()
    rv.points = points_v
    rv.colors = colors_v
    return rv
    
def write_ply_cwipc(filename, pc):
    """Write cwipc pointcloud to PLY file"""
    cwipc.cwipc_write(filename, pc)
    
def write_dump_cwipc(filename, pc):
    """Write cwipc pointcloud to cwipcdump file"""
    cwipc.cwipc_write_debugdump(filename, pc)
    
def main():
    if len(sys.argv) != 5:
        print('Usage: %s loot-source-ply-dir dest-ply-dir dest-cwicpc-dir dest-cwipcdump-dir' % sys.argv[0])
        print('Use - to skip an output format')
        sys.exit(1)
    loot_source_dir = sys.argv[1]
    ply_dest_dir = sys.argv[2]
    cwicpc_dest_dir = sys.argv[3]
    cwipcdump_dest_dir = sys.argv[4]
    if ply_dest_dir == '-': 
        ply_dest_dir = None
    if cwicpc_dest_dir == '-': 
        cwicpc_dest_dir = None
    if cwipcdump_dest_dir == '-': 
        cwipcdump_dest_dir = None
    if ply_dest_dir: 
        os.mkdir(ply_dest_dir)
    if cwicpc_dest_dir: 
        os.mkdir(cwicpc_dest_dir)
        if MAXTILES > 0:
            for i in range(1,MAXTILES+1):
                os.mkdir(cwicpc_dest_dir+str(i))
        if ALSO_LOW:
            os.mkdir(cwicpc_dest_dir+'-low')
            if MAXTILES > 0:
                for i in range(1,MAXTILES+1):
                    os.mkdir(cwicpc_dest_dir+str(i)+'-low')
        
    if cwipcdump_dest_dir: 
        os.mkdir(cwipcdump_dest_dir)
        
        
    startTime = time.time()
    count = 0
    timestamp = 0
    allfiles = os.listdir(loot_source_dir)
    allfiles.sort()
    
    # Setup the encoder group and the encoders
    
    enc_group = cwipc.codec.cwipc_new_encodergroup()
    params = cwipc.codec.cwipc_encoder_params(False, 1, 1.0, 9, 85, 16, 0, 0)
    encoders = []
    encoders.append(enc_group.addencoder(params=params))
    if MAXTILES > 0:
        for i in range(1, MAXTILES+1):
            params.tilenumber = i
            encoders.append(
                enc_group.addencoder(params=params) 
            )
    if ALSO_LOW:
        params_low = cwipc.codec.cwipc_encoder_params(False, 1, 1.0, 7, 60, 16, 0, 0)
        encoders.append(enc_group.addencoder(params=params_low))
        if MAXTILES > 0:
            for i in range(1, MAXTILES+1):
                params_low.tilenumber = i
                encoders.append(
                    enc_group.addencoder(params=params_low) 
                )
            
    for filename in allfiles:
        if os.path.splitext(filename)[1] != '.ply':
            continue
        pathname = os.path.join(loot_source_dir, filename)
        print(pathname, '...')
        basename = os.path.splitext(filename)[0]
        if ply_dest_dir:
            ply_dest_pathname = os.path.join(ply_dest_dir, filename)
        if cwipcdump_dest_dir:
            cwipcdump_dest_pathname = os.path.join(cwipcdump_dest_dir, basename + '.cwipcdump')
       
        if cwicpc_dest_dir:
            cwicpc_dest_pathnames = []
            cwicpc_dest_pathnames.append(os.path.join(cwicpc_dest_dir, basename + '.cwicpc'))
            if MAXTILES > 0:
                for i in range(1,MAXTILES+1):
                    cwicpc_dest_pathnames.append(
                        os.path.join(cwicpc_dest_dir + str(i), basename + '.cwicpc')
                    )
            if ALSO_LOW:
                cwicpc_dest_pathnames.append(os.path.join(cwicpc_dest_dir + '-low', basename + '.cwicpc'))
                if MAXTILES > 0:
                    for i in range(1,MAXTILES+1):
                        cwicpc_dest_pathnames.append(
                            os.path.join(cwicpc_dest_dir + str(i) + '-low', basename + '.cwicpc')
                        )
            
        # Read original loot, downsample and scale.
        o3dpc = read_loot_ply_o3d(pathname)

        # Convert to cwipc
        pc = o3d_to_cwipc(o3dpc, timestamp)

        # Save as a plyfile
        if ply_dest_dir:
            write_ply_cwipc(ply_dest_pathname, pc)
        # Save as dump
        if cwipcdump_dest_dir:
            write_dump_cwipc(cwipcdump_dest_pathname, pc)
        # compress and save
        if cwicpc_dest_dir:
            enc_group.feed(pc)
            for i in range(len(encoders)):
                ok = encoders[i].available(True)
                assert ok
                data = encoders[i].get_bytes()
                with open(cwicpc_dest_pathnames[i], 'wb') as ofp:
                    ofp.write(data)

        pc.free()
        
        timestamp += TIME_INCREMENT
        count += 1
        
    now = time.time()
    print("Converted %d pointclouds in %f seconds" % (count, now-startTime))
    
if __name__ == '__main__':
    main()
    
    
    
