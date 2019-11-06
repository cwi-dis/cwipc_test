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
SKIP_FIRST_GRABS=10 # Skip this many grabs before using one. Needed for D435, it seems.

CONFIGFILE="""<?xml version="1.0" ?>
<file>
    <CameraConfig>
        <system usb2width="640" usb2height="480" usb2fps="15" usb3width="1280" usb3height="720" usb3fps="30" />
        <postprocessing depthfiltering="1" backgroundremoval="1" greenscreenremoval="1" cloudresolution="0" tiling="0" tilingresolution="0.01" tilingmethod="camera">
            <depthfilterparameters threshold_near="{near}" threshold_far="{far}" decimation_value="1" spatial_iterations="4" spatial_alpha="0.25" spatial_delta="30" spatial_filling="0" temporal_alpha="0.4" temporal_delta="20" temporal_percistency="3" />
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

def prompt(msg, isedit=False):
    stars = '*'*(len(msg)+2)
    print(stars)
    print('* ' + msg)
    print()
    print('- Inspect the pointcloud (use drag and mousehweel)')
    print('- Use +/= or -/_ to change point size')
    print('- press q or ESC when done')
    if isedit:
        print('- Select points with shift-leftclick, Deselect points with shift-rightclick')
        print('- Shift +/= or Shift -/_ to change selection indicator size')
        print('- ignore selection indicator colors, only the order is important')
    sys.stdout.flush()
        
def ask(msg, canretry=False):
    answered = False
    while not answered:
        print('* ', msg)
        if canretry:
            print('* Press y if it is fine, n to retry, or control-C to abort')
        else:
            print('* Press y if it is fine, or control-C to abort')
        print('? ', end='')
        sys.stdout.flush()
        answer = sys.stdin.readline().strip().lower()
        ok = answer == 'y'
        answered = ok
        if canretry and answer == 'n':
            answered = True
    return ok
        
class Calibrator:
    def __init__(self, distance):
        if os.path.exists('cameraconfig.xml'):
            print('%s: cameraconfig.xml already exists, please remove if you want to recalibrate' % sys.argv[0])
            sys.exit(1)
        # Set initial config file, for filtering parameters
        self.cameraserial = []
        self.near = 0.5 * distance
        self.far = 2.0 * distance
        self.writeconfig()
        
        self.grabber = cwipc.realsense2.cwipc_realsense2()
        self.pointclouds = []
        self.refpointcloud = None
        self.cameraserial = self.getserials()
        self.matrixinfo = []
        self.winpos = 100
        sys.stdout.flush()

    def getserials(self):
        """Get serial numbers of cameras"""
        rv = []
        ntile = self.grabber.maxtile()
        for i in range(ntile):
            info = self.grabber.get_tileinfo_raw(i)
            if info.camera != None:
                cam_id = info.camera
                cam_id = cam_id.decode('ascii')
                print('Found camera at tile', i, ', camera serial', cam_id)
                rv.append(cam_id)
        return rv
        
    def run(self):
        if not self.cameraserial:
            print('* No realsense cameras found')
            return False
        workdir = os.getcwd()
        print('* Grabbing pointclouds')
        self.get_pointclouds()
        if DEBUG:
            for i in range(len(self.pointclouds)):
                print('Saving pointcloud {} to file'.format(i))
                cwipc.cwipc_write('pc-%d.ply' % i, self.pointclouds[i])
        #
        # First show the pointclouds for visual inspection.
        #
        grab_ok = False
        while not grab_ok:
            sys.stdout.flush()
            for i in range(len(self.pointclouds)):
                prompt(f'Showing grabbed pointcloud from camera {i} for visual inspection')
                pcd = self.cwipc_to_o3d(self.pointclouds[i])
                self.show_points(self.cameraserial[i], pcd)
            grab_ok = ask('Can you select the balls on the cross from this pointcloud?', canretry=True)
            if not grab_ok:
                print('* Grabbing pointclouds again')
                self.pointclouds = []
                self.get_pointclouds()
        
        prompt('Pick red, orange, yellow, blue points on reference image', isedit=True)
        #
        # Pick reference points
        #
        o3drefpointcloud = self.cwipc_to_o3d(self.refpointcloud)
        refpoints = self.pick_points('reference', o3drefpointcloud)
        
        #
        # Pick points in images
        #
        for i in range(len(self.pointclouds)):
            matrix_ok = False
            while not matrix_ok:
                prompt(f'Pick red, orange, yellow, blue points on camera {i} pointcloud', isedit=True)
                pcd = self.cwipc_to_o3d(self.pointclouds[i])
                pc_refpoints = self.pick_points(self.cameraserial[i], pcd)
                info = self.align_pair(pcd, pc_refpoints, o3drefpointcloud, refpoints, False)
                prompt(f'Inspect resultant orientation of camera {i} pointcloud')
                self.show_points(self.cameraserial[i], o3drefpointcloud, self.cwipc_to_o3d(self.pointclouds[i], info))
                matrix_ok = ask('Does that look good?', canretry=True)
            self.matrixinfo.append(info)
        #
        # Show result
        #
        allclouds = [o3drefpointcloud]
        for i in range(len(self.pointclouds)):
            
            allclouds.append(self.cwipc_to_o3d(self.pointclouds[i], self.matrixinfo[i]))
        prompt('Inspect the resultant merged pointclouds of all cameras')
        self.show_points('all', *tuple(allclouds))
        # Open3D Visualiser changes directory (!!?!), so change it back
        os.chdir(workdir)
        self.writeconfig()
        self.save_pcds('cwipc_calibrate_calibrated.ply', *tuple(allclouds[1:]))
        self.cleanup()
        
    def cleanup(self):
        for p in self.pointclouds:
            p.free()
        self.pointclouds = []
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
            (-1, 0, -1, 0, 0, 0),             # Black point at -1,0,-1
            (-1, 0, 1, 0, 0, 0),             # Black point at -1,0,1
            (1, 0, -1, 0, 0, 0),             # Black point at 1,0,-1
            (1, 0, 1, 0, 0, 0),             # Black point at 1,0,1
            (0, 1, 0, 0, 0, 0),             # Black point at cross
            (0, 1.1, 0, 0, 0, 0),           # Black point at forward spar
        ]
        self.refpointcloud = cwipc.cwipc_from_points(points_0, 0)
        # Get the number of cameras and their tile numbers
        tiles = []
        maxtile = self.grabber.maxtile()
        if DEBUG: print('maxtile', maxtile)
        if maxtile == 1:
            tiles.append(0)
        else:
            for i in range(1, maxtile):
                info = self.grabber.get_tileinfo_dict(i)
                if DEBUG: print('info', i, info)
                if info != None and info['ncamera'] == 1:
                    tiles.append(i)
        # Grab one combined pointcloud and split it into tiles
        for i in range(SKIP_FIRST_GRABS):
            pc = self.grabber.get()
            pc.free()
        pc = self.grabber.get()
        if DEBUG: cwipc.cwipc_write('cwipc_calibrate_captured.ply', pc)
        for tilenum in tiles:
            pc_tile = cwipc.codec.cwipc_tilefilter(pc, tilenum)
            print('Grabbed pointcloud for tile {} to self.pointclouds[{}]'.format(tilenum, len(self.pointclouds)))
            self.pointclouds.append(pc_tile)  
        # xxxjack
        allo3dpcs = map(self.cwipc_to_o3d, tuple([self.refpointcloud] + self.pointclouds))
        if DEBUG: self.save_pcds('cwipc_calibrate_uncalibrated.ply', *allo3dpcs)
        
    def pick_points(self, title, pcd):
        vis = open3d.VisualizerWithEditing()
        vis.create_window(window_name=title, width=960, height=540, left=self.winpos, top=self.winpos)
        self.winpos += 50
        vis.add_geometry(pcd)
        vis.run() # user picks points
        vis.destroy_window()
        return vis.get_picked_points()

    def show_points(self, title, *pcds):
        vis = open3d.Visualizer()
        vis.create_window(window_name=title, width=960, height=540, left=self.winpos, top=self.winpos)
        self.winpos += 50
        for pcd in pcds:
            vis.add_geometry(pcd)
        vis.run()
        vis.destroy_window()

    def save_pcds(self, filename, *pcds):
        pc = self.o3d_to_cwipc(*pcds)
        cwipc.cwipc_write(filename, pc)
        pc.free()
        
    def cwipc_to_o3d(self, pc, matrix=None):
        """Convert cwipc pointcloud to open3d pointcloud"""
        # Note that this method is inefficient, it can probably be done
        # in-place with some numpy magic
        pcpoints = pc.get_points()
        points = []
        colors = []
        for p in pcpoints:
            points.append([p.x, p.y, p.z])  
            colors.append((float(p.r)/255.0, float(p.g)/255.0, float(p.b)/255.0))
        points_v_np = np.matrix(points)
        if not matrix is None:
            submatrix = matrix[:3, :3]
            translation = matrix[:3, 3]
            points_v_np = (submatrix * points_v_np.T).T
            points_v_np = points_v_np + translation
        points_v = open3d.Vector3dVector(points_v_np)
        colors_v = open3d.Vector3dVector(colors)
        rv = open3d.PointCloud()
        rv.points = points_v
        rv.colors = colors_v
        return rv

    def o3d_to_cwipc(self, *o3dclouds):
        tilenum = 1
        cwiPoints = None
        for o3dcloud in o3dclouds:
            points = o3dcloud.points
            colors = o3dcloud.colors
            tiles = np.array([[tilenum]]*len(points))
            thisPoints = np.hstack((points, colors, tiles))
            if cwiPoints is None:
                cwiPoints = thisPoints
            else:
                cwiPoints = np.vstack((cwiPoints, thisPoints))
            tilenum = tilenum*2
        cwiPoints = list(map(lambda p : (p[0],p[1],p[2],int(p[3]*255),int(p[4]*255),int(p[5]*255), int(p[6])), list(cwiPoints)))
        pc = cwipc.cwipc_from_points(cwiPoints, 0)
        return pc
        
    def align_pair(self, source, picked_id_source, target, picked_id_target, extended=False):
        assert(len(picked_id_source)>=3 and len(picked_id_target)>=3)
        assert(len(picked_id_source) == len(picked_id_target))
        corr = np.zeros((len(picked_id_source),2))
        corr[:,0] = picked_id_source
        corr[:,1] = picked_id_target

        p2p = open3d.TransformationEstimationPointToPoint()
        trans_init = p2p.compute_transformation(source, target,
                 open3d.Vector2iVector(corr))
        
        if not extended:
            return trans_init

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
        fileinfo = CONFIGFILE.format(cameras=allcaminfo, near=self.near, far=self.far)
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
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} distance\nWhere distance is approximate distance between cameras and (0,0) point (in meters)")
        sys.exit(1)
    distance = float(sys.argv[1])
    prog = Calibrator(distance)
    prog.run()
    
if __name__ == '__main__':
    main()
    
    
    
