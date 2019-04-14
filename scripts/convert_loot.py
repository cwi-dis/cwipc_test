import sys
import os
import open3d
import numpy as np
import cwipc
import cwipc.codec
import time

VOXEL_SIZE = 3.5    # Larger numbers mean smaller output size
SCALE_FACTOR = 500  # Conversion factor from loot xyz values to our xyz values
TIME_INCREMENT = 33333 # Increment in timestamp between successive pointclouds

def read_loot_ply_o3d(filename):
    """Read PLY file using open3d, scale it and downsample it. Returns open3d pointcloud"""
    original = open3d.read_point_cloud(filename)
    downsampled = open3d.voxel_down_sample(original, voxel_size=VOXEL_SIZE)
    points = np.asarray(downsampled.points)
    points /= SCALE_FACTOR
    return downsampled
    
def write_ply_o3d(filename, o3dpc):
    """Write PLY file from open3d pointcloud"""
    open3d.write_point_cloud(filename, o3dpc, write_ascii=True)
    
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
        r = int(r*255)
        g = int(g*255)
        b = int(b*255)
        rv.append((x, y, z, r, g, b))
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
    
def main():
    if len(sys.argv) != 4:
        print('Usage: %s loot-source-ply-dir dest-ply-dir dest-cwicpc-dir' % sys.argv[0])
        sys.exit(1)
    loot_source_dir = sys.argv[1]
    ply_dest_dir = sys.argv[2]
    cwicpc_dest_dir = sys.argv[3]
    os.mkdir(ply_dest_dir)
    os.mkdir(cwicpc_dest_dir)
    
    startTime = time.time()
    count = 0
    timestamp = 0
    for filename in os.listdir(loot_source_dir):
        if os.path.splitext(filename)[1] != '.ply':
            continue
        pathname = os.path.join(loot_source_dir, filename)
        print(pathname, '...')
        basename = os.path.splitext(filename)[0]
        ply_dest_pathname = os.path.join(ply_dest_dir, filename)
        cwicpc_dest_pathname = os.path.join(cwicpc_dest_dir, basename + '.cwicpc')
        
        # Read original loot, downsample and scale.
        o3dpc = read_loot_ply_o3d(pathname)

        # Convert to cwipc
        pc = o3d_to_cwipc(o3dpc, timestamp)

        # Save as a plyfile
        write_ply_cwipc(ply_dest_pathname, pc)
        
        # compress and save
        enc = cwipc.codec.cwipc_new_encoder()
        enc.feed(pc)
        gotData = enc.available(True)
        assert gotData
        data = enc.get_bytes()
        assert data
        with open(cwicpc_dest_pathname, 'wb') as ofp:
            ofp.write(data)
        pc.free()
        enc.free()
        
        timestamp += TIME_INCREMENT
        count += 1
        
    now = time.time()
    print("Converted %d pointclouds in %f seconds" % (count, now-startTime))
    
if __name__ == '__main__':
    main()
    
    
    
