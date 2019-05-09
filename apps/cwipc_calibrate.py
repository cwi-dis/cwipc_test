import sys
import os
import time
import socket
import argparse
import traceback
import cwipc
import cwipc.codec
import cwipc.realsense2
import numpy as np
import open3d

DEBUG=False

CONFIGFILE="""<?xml version="1.0" ?>
<file>
    <CameraConfig>
        <system usb2width="640" usb2height="480" usb2fps="15" usb3width="1280" usb3height="720" usb3fps="30" />
        <postprocessing depthfiltering="0" backgroundremoval="1" greenscreenremoval="1" cloudresolution="0" tiling="0" tilingresolution="0.01" tilingmethod="camera">
            <depthfilterparameters decimation_value="2" spatial_iterations="4" spatial_alpha="0.25" spatial_delta="30" spatial_filling="0" temporal_alpha="0.4" temporal_delta="20" temporal_percistency="3" />
        </postprocessing>
        {cameras}
    </CameraConfig>
</file>
"""
CONFIGCAMERA="""
        <camera serial="{serial}" backgroundx="0" backgroundy="0" backgroundz="0">
            <trafo>
                {matrixinfo}
            </trafo>
        </camera>
"""
class Calibrator:
    def __init__(self, nosend=False, port=4303, count=None, plydir=None, cwicpcdir=None, params=None):
        self.grabber = cwipc.realsense2.cwipc_realsense2()
        self.pointclouds = []
        self.o3dpointclouds = []
        self.refpointcloud = None
        self.cameraserial = []
        self.matrixinfo = []

    def run(self):
        self.get_pointclouds()
        if DEBUG:
            for i in range(len(self.pointclouds)):
                cwipc.cwipc_write('pc-%d.ply' % i, self.pointclouds[i])
        for i in range(len(self.pointclouds)):
            print('Enter serial number for camera', i+1, '-')
            sys.stdout.flush()
            line = sys.stdin.readline()
            self.cameraserial.append(line.strip())
            
        o3drefpointcloud = self.cwipc_to_o3d(self.refpointcloud)
        refpoints = self.pick_points(o3drefpointcloud)
        
        for i in range(len(self.pointclouds)):
            pcd = self.cwipc_to_o3d(self.pointclouds[i])
            self.o3dpointclouds.append(pcd)
            pc_refpoints = self.pick_points(pcd)
            info = self.align_pair(pcd, pc_refpoints, o3drefpointcloud, refpoints)
            self.matrixinfo.append(info)
        self.writeconfig()
        self.cleanup()
        
    def cleanup(self):
        for p in self.pointclouds:
            p.free()
        self.pointclouds = []
        self.o3dpointclouds = []
        self.refpointcloud.free()
        self.refpointcloud = None
        self.grabber.free()
        self.grabber = None
        
    def get_pointclouds(self):
        # Create the canonical pointcloud, which determines the eventual coordinate system
        points_0 = [
            (0.25, 1, 0, 255, 0, 0),        # Red ball at Right of the cross
            (0, 1.25, 0, 0, 0, 255),        # Blue ball at top of the cross (because the sky is blue)
            (0, 1.1, -0.25, 255, 127, 0),   # Orange ball pointing towards the viewer (-Z) because everyone likes orange
            (-0.25, 1, 0, 255, 255, 0),     # Yellow ball at left of cross because it had to go somewhere
            (0, 0, 0, 0, 0, 0),             # Black point at 0,0,0
            (0, 1, 0, 0, 0, 0),             # Black point at cross
            (0, 1.1, 0, 0, 0, 0),           # Black point at forward spar
        ]
        self.refpointcloud = cwipc.cwipc_from_points(points_0, 0)
        
        # Get the number of cameras and their tile numbers
        tiles = []
        maxtile = self.grabber.maxtile()
        if DEBUG: print('maxtile', maxtile)
        for i in range(1, maxtile):
            info = self.grabber.get_tileinfo_dict(i)
            if DEBUG: print('info', i, info)
            if info != None:
                tiles.append(i)
        # Grab one combined pointcloud and split it into tiles
        pc = self.grabber.get()
        if DEBUG: cwipc.cwipc_write('pcall.ply', pc)
        for tilenum in tiles:
            pc_tile = cwipc.codec.cwipc_tilefilter(pc, tilenum)
            self.pointclouds.append(pc_tile)  
    
    def pick_points(self, pcd):
        vis = open3d.VisualizerWithEditing()
        vis.create_window()
        vis.add_geometry(pcd)
        vis.run() # user picks points
        vis.destroy_window()
        return vis.get_picked_points()

    def cwipc_to_o3d(self, pc):
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

    def align_pair(self, source, picked_id_source, target, picked_id_target):
        assert(len(picked_id_source)>=3 and len(picked_id_target)>=3)
        assert(len(picked_id_source) == len(picked_id_target))
        corr = np.zeros((len(picked_id_source),2))
        corr[:,0] = picked_id_source
        corr[:,1] = picked_id_target

        p2p = open3d.TransformationEstimationPointToPoint()
        trans_init = p2p.compute_transformation(source, target,
                 open3d.Vector2iVector(corr))

        threshold = 0.01 # 3cm distance threshold
        reg_p2p = open3d.registration_icp(source, target, threshold, trans_init,
                open3d.TransformationEstimationPointToPoint())
        
        return reg_p2p.transformation
    
    def writeconfig(self):
        allcaminfo = ""
        for i in range(len(self.cameraserial)):
            serial = self.cameraserial[i]
            matrixinfo = self.to_conf(self.matrixinfo[i])
            caminfo = CONFIGCAMERA.format(serial=serial, matrixinfo=matrixinfo)
            allcaminfo += caminfo
        fileinfo = CONFIGFILE.format(cameras=allcaminfo)
        with open('cameraconfig.xml', 'w') as fp:
            fp.write(fileinfo)
 
    def to_conf(self, trans):
        s = "<values "
        for i in range(4):
            for j in range(4):
                s += f'v{i}{j}="{trans[i][j]}" '
                
        s += " />"
        return s   

            
def main():
    parser = argparse.ArgumentParser(description="Calibrate a number of realsense cameras")
    args = parser.parse_args()
    prog = Calibrator()
    prog.run()
    
if __name__ == '__main__':
    main()
    
    
    
