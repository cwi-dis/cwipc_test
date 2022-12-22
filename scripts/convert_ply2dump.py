import sys
import os
import open3d
import numpy as np
import cwipc
import cwipc.codec
import cwipc.util
import time

VOXEL_SIZE = 1    # Larger numbers mean smaller output size
SCALE_FACTOR = 550  # Conversion factor from loot xyz values to our xyz values
TRANSLATE_X = -0.35 # Conversion (after scaling) of X values
TRANSLATE_Y = 0     # Conversion (after scaling) of Y values
TRANSLATE_Z = -0.35 # Conversion (after scaling) of Z values
TIME_INCREMENT = 33 # Increment in timestamp between successive pointclouds

MAXTILES=4  # Number of tiles (in addition to tile 0) to encode
ALSO_LOW=True   # Set to True to also do low quality cwicpc

def read_loot_ply_o3d(filename):
    """Read PLY file using open3d, scale it and downsample it. Returns open3d pointcloud"""
    original = open3d.io.read_point_cloud(filename)
    #downsampled = open3d.voxel_down_sample(original, voxel_size=VOXEL_SIZE)
    downsampled = original
    points = np.asarray(downsampled.points)
    min_point = points.min(axis=0)
    max_point = points.max(axis=0)
    print(f"x: {TRANSLATE_X+min_point[0]/SCALE_FACTOR}..{TRANSLATE_X+max_point[0]/SCALE_FACTOR}")
    print(f"y: {TRANSLATE_Y+min_point[1]/SCALE_FACTOR}..{TRANSLATE_Y+max_point[1]/SCALE_FACTOR}")
    print(f"z: {TRANSLATE_Z+min_point[2]/SCALE_FACTOR}..{TRANSLATE_Z+max_point[2]/SCALE_FACTOR}")
    translate = np.array([TRANSLATE_X, TRANSLATE_Y, TRANSLATE_Z])
    points /= SCALE_FACTOR
    points += translate
    return downsampled
    
def write_ply_o3d(filename, o3dpc):
    """Write PLY file from open3d pointcloud"""
    open3d.io.write_point_cloud(filename, o3dpc, write_ascii=True)
    
def draw_o3d(o3dpc):
    """Draw open3d pointcloud"""
    open3d.draw_geometries([o3dpc])
    
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
    points_v = open3d.Vector3dVector(points)
    colors_v = open3d.Vector3dVector(colors)
    rv = open3d.PointCloud()
    rv.points = points_v
    rv.colors = colors_v
    return rv
    
def write_ply_cwipc(filename, pc):
    """Write cwipc pointcloud to PLY file"""
    cwipc.cwipc_write(filename, pc)
    
def write_dump_cwipc(filename, pc):
    """Write cwipc pointcloud to PLY file"""
    cwipc.cwipc_write_debugdump(filename, pc)
    
def main():
    if len(sys.argv) != 3:
        print('Usage: %s source-ply-dir dest-dump-dir [pointsize]' % sys.argv[0])
        sys.exit(1)
    loot_source_dir = sys.argv[1]
    dump_dest_dir = sys.argv[2]
    pointsize = 0
    if len(sys.argv) > 3:
        pointsize = float(sys.argv[3])
    if not os.path.exists(dump_dest_dir):
        os.mkdir(dump_dest_dir)

    startTime = time.time()
    count = 0
    timestamp = 0
    allfiles = os.listdir(loot_source_dir)
    allfiles.sort()
    
            
    for filename in allfiles:
        if os.path.splitext(filename)[1] != '.ply':
            continue
        pathname = os.path.join(loot_source_dir, filename)
        print(pathname, '...')
        basename = os.path.splitext(filename)[0]
        dump_dest_pathname = os.path.join(dump_dest_dir, basename + '.cwipcdump')
        # Read original loot, downsample and scale.
        o3dpc = read_loot_ply_o3d(pathname)

        # Convert to cwipc
        pc = o3d_to_cwipc(o3dpc, timestamp)
        
        # Set the pointsize (guessed)
        pc._setcellsize(pointsize)
        
        #save as dump
        write_dump_cwipc(dump_dest_pathname, pc)


        pc.free()
        
        timestamp += TIME_INCREMENT
        count += 1
        
    now = time.time()
    print("Converted %d pointclouds in %f seconds" % (count, now-startTime))
    
if __name__ == '__main__':
    main()
    
    
    
