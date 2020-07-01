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
import xml.etree.ElementTree as ET
import argparse

DEBUG=False
SKIP_FIRST_GRABS=10 # Skip this many grabs before using one. Needed for D435, it seems.

CONFIGFILE="""<?xml version="1.0" ?>
<file>
    <CameraConfig>
        <system usb2width="640" usb2height="480" usb2fps="15" usb3width="1280" usb3height="720" usb3fps="30" />
        <postprocessing density="1" height_min="0" height_max="0" depthfiltering="1" backgroundremoval="0" greenscreenremoval="0" cloudresolution="0" tiling="0" tilingresolution="0.01" tilingmethod="camera">
            <depthfilterparameters {distance} decimation_value="1" spatial_iterations="4" spatial_alpha="0.25" spatial_delta="30" spatial_filling="0" temporal_alpha="0.4" temporal_delta="20" temporal_percistency="3" />
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
#
# Version 2 calibration cross: the one made with little balls and the forward spar
#
POINTS_V2 = [
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
#
# Version 3 calibration cross: the one with the leds and the uneven arms
#
POINTS_V3 = [
    (-0.26, 1.04, 0, 255, 0, 0),        # Red LED at left of the cross
    (0, 1.44, 0, 0, 0, 255),        # Blue LED at top of the cross (because the sky is blue)
    (0, 1.31, -0.26, 0, 255, 0),   # Green LED pointing towards the viewer (-Z)
    (0.26, 1.17, 0, 255, 255, 0),     # Yellow LED at right of cross because it had to go somewhere
    (0, 0, 0, 0, 0, 0),             # Black point at 0,0,0
    (-1, 0, -1, 0, 0, 0),             # Black point at -1,0,-1
    (-1, 0, 1, 0, 0, 0),             # Black point at -1,0,1
    (1, 0, -1, 0, 0, 0),             # Black point at 1,0,-1
    (1, 0, 1, 0, 0, 0),             # Black point at 1,0,1
]

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
        
class Pointcloud:
    """A class that handles both cwipc pointclouds and o3d pointclouds and converts between them"""
    
    def __init__(self):
        self.cwipc = None
        self.o3d = None
        
    def __del__(self):
        if self.cwipc:
            self.cwipc.free()
        self.cwipc = None
        self.o3d = None
        
    def _ensure_cwipc(self):
        """Internal - make sure the cwipc is valid"""
        if self.cwipc: return
        tilenum = 1
        points = self.o3d.points
        colors = self.o3d.colors
        tiles = np.array([[tilenum]]*len(points))
        cwiPoints = np.hstack((points, colors, tiles))
        cwiPoints = list(map(lambda p : (p[0],p[1],p[2],int(p[3]*255),int(p[4]*255),int(p[5]*255), int(p[6])), list(cwiPoints)))
        self.cwipc = cwipc.cwipc_from_points(cwiPoints, 0)
        
    def _ensure_o3d(self):
        """internal - make sure the o3d pc is valid"""
        if self.o3d: return
        # Note that this method is inefficient, it can probably be done
        # in-place with some numpy magic
        assert self.cwipc
        pcpoints = self.cwipc.get_points()
        points = []
        colors = []
        for p in pcpoints:
            points.append([p.x, p.y, p.z])  
            colors.append((float(p.r)/255.0, float(p.g)/255.0, float(p.b)/255.0))
        points_v_np = np.matrix(points)
        points_v = open3d.utility.Vector3dVector(points_v_np)
        colors_v = open3d.utility.Vector3dVector(colors)
        self.o3d = open3d.geometry.PointCloud()
        self.o3d.points = points_v
        self.o3d.colors = colors_v
        
    @classmethod
    def from_cwipc(klass, pc):
        """Create Pointcloud from cwipc"""
        self = klass()
        self.cwipc = pc
        return self

    @classmethod
    def from_o3d(klass, o3d):
        """Create Pointcloud from o3d pc"""
        self = klass()
        self.o3d = o3d
        return self
        
    @classmethod
    def from_points(klass, points):
        """Create Pointcloud from list of xyzrgbt tuples"""
        self = klass()
        pc = cwipc.cwipc_from_points(points, 0)
        self.cwipc = pc
        return self
        
    @classmethod
    def from_file(klass, filename):
        """Create Pointcloud from ply file"""
        self = klass()
        pc = cwipc.cwipc_read(filename)
        self.cwipc = pc
        return self
        
    @classmethod
    def from_join(klass, *pointclouds):
        """Create tiled Pointcloud from separate pointclouds"""
        allPoints = []
        tileNum = 1
        for src_pc in pointclouds:
            src_cwipc = src_pc.get_cwipc()
            points = src_cwipc.get_points()
            points = map(lambda p : (p.x, p.y, p.z, p.r, p.g, p.b, tileNum), points)
            allPoints += points
            tileNum *= 2
        return klass.from_points(allPoints)
        
    def get_cwipc(self):
        """Return cwipc object"""
        self._ensure_cwipc()
        return self.cwipc
        
    def get_o3d(self):
        """Return o3d pc object"""
        self._ensure_o3d()
        return self.o3d
        
    def save(self, filename):
        """Save to PLY file"""
        self._ensure_cwipc()
        cwipc.cwipc_write(filename, self.cwipc)
        
    def split(self):
        """Split into per-tile Pointcloud objects"""
        self._ensure_cwipc()
        alltiles = set()
        #
        # This is stupid code, because we should really get a list of tilenumbers as parameter.
        # The current code depends on the serial numbers having been collected in tile-number-order.
        #
        for pt in self.cwipc.get_points():
            alltiles.add(pt.tile)
        rv = []
        alltiles = list(alltiles)
        alltiles.sort()
        for tilenum in alltiles:
            tile_pc = cwipc.codec.cwipc_tilefilter(self.cwipc, tilenum)
            rv.append(self.__class__.from_cwipc(tile_pc))
        return rv
        
    def transform(self, matrix):
        """Return pointcloud multiplied by a matrix"""
        # Note that this method is inefficient, it can probably be done
        # in-place with some numpy magic
        self._ensure_cwipc()
        pcpoints = self.cwipc.get_points()
        points = []
        colort = []
        for p in pcpoints:
            points.append([p.x, p.y, p.z])  
            colort.append((p.r, p.g, p.b, p.tile))
        npPoints = np.matrix(points)
        submatrix = matrix[:3, :3]
        translation = matrix[:3, 3]
        npPoints = (submatrix * npPoints.T).T
        npPoints = npPoints + translation
        assert len(npPoints) == len(points)
        newPoints = []
        for i in range(len(points)):
            newPoint = tuple(npPoints[i].tolist()[0]) + colort[i]
            newPoints.append(newPoint)
        return self.__class__.from_points(newPoints)
        
    def bbox(self, bbox):
        """Return pointcloud limited to a bounding box"""
        x0, x1, y0, y1, z0, z1 = bbox
        self._ensure_cwipc()
        pcpoints = self.cwipc.get_points()
        newPoints = []
        for p in pcpoints:
            if p.x < x0 or p.x > x1:
                continue
            if p.y < y0 or p.y > y1:
                continue
            if p.z < z0 or p.z > z1:
                continue
            newPoints.append(p)
        return self.__class__.from_points(newPoints)

class LiveGrabber:
    def __init__(self):
        self.grabber = None
        self.grabber = cwipc.realsense2.cwipc_realsense2()
        # May need to grab a few combined pointclouds and throw them away
        for i in range(SKIP_FIRST_GRABS):
            pc = self.grabber.get()
            pc.free()
   
    def __del__(self):
        if self.grabber: self.grabber.free()
        self.grabber = None
    
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
        
    def getmatrix(self, tilenum):
        return [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
        
    def getcount(self):
        # Get the number of cameras and their tile numbers
        tiles = []
        maxtile = self.grabber.maxtile()
        if DEBUG: print('maxtile', maxtile)
        if maxtile == 1:
            return 1
        else:
            for i in range(1, maxtile):
                info = self.grabber.get_tileinfo_dict(i)
                if DEBUG: print('info', i, info)
                if info != None and info['ncamera'] == 1:
                    tiles.append(i)
        # Check that the tile numbers or a bitmap, as we expect (in join, for example)
        for i in range(len(tiles)):
            assert tiles[i] == (1<<i)
        return len(tiles)
        
    def getpointcloud(self):
        pc = self.grabber.get()
        assert pc
        return Pointcloud.from_cwipc(pc)

class FileGrabber:
    def __init__(self, dirname):
        self.pcFilename = os.path.join(dirname, "cwipc_calibrate_calibrated.ply")
        confFilename = os.path.join(dirname, "cameraconfig.xml")
        self.serials = []
        self.matrices = []
        self._parseConf(confFilename)
        
    def _parseConf(self, confFilename):
        tree = ET.parse(confFilename)
        root = tree.getroot()
        for camElt in root.findall('CameraConfig/camera'):
            serial = camElt.attrib['serial']
            assert serial
            trafoElts = list(camElt.iter('trafo'))
            assert len(trafoElts) == 1
            trafoElt = trafoElts[0]
            valuesElts = list(trafoElt.iter('values'))
            assert len(valuesElts) == 1
            valuesElt = valuesElts[0]
            va = valuesElt.attrib
            trafo = [
                [float(va['v00']), float(va['v01']), float(va['v02']), float(va['v03'])],
                [float(va['v10']), float(va['v11']), float(va['v12']), float(va['v13'])],
                [float(va['v20']), float(va['v21']), float(va['v22']), float(va['v23'])],
                [float(va['v30']), float(va['v31']), float(va['v32']), float(va['v33'])],
            ]
            self.serials.append(serial)
            self.matrices.append(trafo)
        # import pdb ; pdb.set_trace()
        
    def getcount(self):
        return len(self.serials)
        
    def getserials(self):
        return self.serials
        
    def getmatrix(self, tilenum):
        return self.matrices[tilenum]
        
    def getpointcloud(self):
        pc = cwipc.cwipc_read(self.pcFilename, 0)
        return Pointcloud.from_cwipc(pc)
            
class Calibrator:
    def __init__(self, distance, use_v3):
        self.cameraserial = []
        self.near = 0.5 * distance
        self.far = 2.0 * distance
        self.use_v3 = use_v3
        self.grabber = None
        self.cameraserial = []
        self.pointclouds = []
        self.coarse_calibrated_pointclouds = []
        self.fine_calibrated_pointclouds = []
        self.refpointcloud = None
        self.coarse_matrix = []
        self.fine_matrix = []
        self.winpos = 100
        self.workdir = os.getcwd() # o3d visualizer can change directory??!?
        sys.stdout.flush()
        
    def __del__(self):
        self.grabber = None
        self.pointclouds = None
        self.coarse_calibrated_pointclouds = None
        self.refpointcloud = None
        
    def open(self, grabber, clean, reuse):
        if reuse:
            assert 0, "--reuse not yet implemented"
        elif clean:
            if os.path.exists('cameraconfig.xml'):
                os.unlink('cameraconfig.xml')
        if os.path.exists('cameraconfig.xml'):
            print('%s: cameraconfig.xml already exists, please supply --clean or --reuse argument' % sys.argv[0])
            sys.exit(1)
        # Set initial config file, for filtering parameters
        self.writeconfig()
        self.grabber = grabber
        self.cameraserial = self.grabber.getserials()

    def grab(self, noinspect):
        if not self.cameraserial:
            print('* No realsense cameras found')
            return False
        print('* Grabbing pointclouds')
        self.get_pointclouds()
        if DEBUG:
            for i in range(len(self.pointclouds)):
                print('Saving pointcloud {} to file'.format(i))
                self.pointclouds[i].save('pc-%d.ply' % i)
        #
        # First show the pointclouds for visual inspection.
        #
        if noinspect: return
        grab_ok = False
        while not grab_ok:
            sys.stdout.flush()
            for i in range(len(self.pointclouds)):
                prompt(f'Showing grabbed pointcloud from camera {i} for visual inspection')
                self.show_points(f'Inspect grab from {self.cameraserial[i]}', self.pointclouds[i])
            grab_ok = ask('Can you select the balls on the cross from this pointcloud?', canretry=True)
            if not grab_ok:
                print('* discarding 10 pointclouds')
                for i in range(10):
                    self.get_pointclouds()
                print('* Grabbing pointclouds again')
                self.pointclouds = []
                self.get_pointclouds()
        
        
    def run_coarse(self):
        prompt('Pick red, orange, yellow, blue points on reference image', isedit=True)
        #
        # Pick reference points
        #
        refpoints = self.pick_points('Pick points on reference', self.refpointcloud)
        
        #
        # Pick points in images
        #
        for i in range(len(self.pointclouds)):
            matrix_ok = False
            while not matrix_ok:
                prompt(f'Pick red, orange, yellow, blue points on camera {i} pointcloud', isedit=True)
                pc_refpoints = self.pick_points(f'Pick points on {self.cameraserial[i]}', self.pointclouds[i])
                info = self.align_pair(self.pointclouds[i], pc_refpoints, self.refpointcloud, refpoints, False)
                prompt(f'Inspect resultant orientation of camera {i} pointcloud')
                new_pc = self.pointclouds[i].transform(info)
                self.show_points(f'Pick points on {self.cameraserial[i]}', new_pc)
                matrix_ok = ask('Does that look good?', canretry=True)
            assert len(self.coarse_matrix) == i
            assert len(self.coarse_calibrated_pointclouds) == i
            self.coarse_matrix.append(info)
            self.coarse_calibrated_pointclouds.append(new_pc)
        #
        # Show result
        #
        prompt('Inspect the resultant merged pointclouds of all cameras')
        joined = Pointcloud.from_join(*tuple(self.coarse_calibrated_pointclouds))
        os.chdir(self.workdir)
        joined.save('cwipc_calibrate_coarse.ply')
        self.show_points('Inspect manual calibration result', joined)
        
    def skip_coarse(self):
        self.coarse_calibrated_pointclouds = self.pointclouds
        for i in range(len(self.cameraserial)):
            self.coarse_matrix.append([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ])
        
    def run_fine(self, bbox, correspondence):
        for i in range(len(self.cameraserial)):
            self.fine_matrix.append([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ])
        if bbox:
            # Apply bounding box to pointclouds
            for i in range(len(self.coarse_calibrated_pointclouds)):
                self.coarse_calibrated_pointclouds[i] = self.coarse_calibrated_pointclouds[i].bbox(bbox)
        if len(self.coarse_calibrated_pointclouds) <= 1:
            print('* Skipping fine-grained calibration: only one camera')
            self.fine_calibrated_pointclouds = self.coarse_calibrated_pointclouds
            return
        joined = Pointcloud.from_join(*tuple(self.coarse_calibrated_pointclouds))
        prompt('Inspect pointcloud after applying bounding box, before fine-grained calibration')
        self.show_points('Inspect bounding box result', joined)
        # We will align everything to the first camera
        refPointcloud = self.coarse_calibrated_pointclouds[0]
        assert len(self.fine_calibrated_pointclouds) == 0
        self.fine_calibrated_pointclouds.append(refPointcloud)
        
        for i in range(1, len(self.coarse_calibrated_pointclouds)):
            srcPointcloud =  self.coarse_calibrated_pointclouds[i]
            newMatrix = self.align_fine(refPointcloud,srcPointcloud, correspondence)
            newPointcloud = srcPointcloud.transform(newMatrix)
            self.fine_calibrated_pointclouds.append(newPointcloud)
            self.fine_matrix[i] = newMatrix
            # print('xxxjack new matrix', newMatrix)
        prompt('Inspect the resultant merged pointclouds of all cameras')
        joined = Pointcloud.from_join(*tuple(self.fine_calibrated_pointclouds))
        os.chdir(self.workdir)
        joined.save('cwipc_calibrate_calibrated.ply')
        self.show_points('Inspect fine calibration result', joined)
        
    def skip_fine(self):
        for i in range(len(self.cameraserial)):
            self.fine_matrix.append([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ])
        self.fine_calibrated_pointclouds = self.coarse_calibrated_pointclouds
        
    def save(self):
        # Open3D Visualiser changes directory (!!?!), so change it back
        os.chdir(self.workdir)
        self.writeconfig()
        self.cleanup()
        
    def cleanup(self):
        self.pointclouds = []
        self.coarse_calibrated_pointclouds = []
        self.fine_calibrated_pointclouds = []
        self.refpointcloud = None
        self.grabber = None
        
    def get_pointclouds(self):
        # Create the canonical pointcloud, which determines the eventual coordinate system
        if self.use_v3:
            self.refpointcloud = Pointcloud.from_points(POINTS_V3)
        else:
            self.refpointcloud = Pointcloud.from_points(POINTS_V2)
        # Get the number of cameras and their tile numbers
        maxtile = self.grabber.getcount()
        if DEBUG: print('maxtile', maxtile)
        # Grab one combined pointcloud and split it into tiles
        for i in range(10):
            pc = self.grabber.getpointcloud()
            if DEBUG: pc.save('cwipc_calibrate_captured.ply')
            self.pointclouds = pc.split()
            if len(self.pointclouds) == maxtile: break
            print(f'Warning: got {len(self.pointclouds)} pointclouds in stead of {maxtile}. Retry.')
        assert len(self.pointclouds) == maxtile
        # xxxjack
        if DEBUG:
            joined = Pointcloud.from_join(self.pointclouds)
            joined.save('cwipc_calibrate_uncalibrated.ply')
        
    def pick_points(self, title, pc):
        vis = open3d.visualization.VisualizerWithEditing()
        vis.create_window(window_name=title, width=960, height=540, left=self.winpos, top=self.winpos)
        self.winpos += 50
        vis.add_geometry(pc.get_o3d())
        vis.run() # user picks points
        vis.destroy_window()
        return vis.get_picked_points()

    def show_points(self, title, pc):
        vis = open3d.visualization.Visualizer()
        vis.create_window(window_name=title, width=960, height=540, left=self.winpos, top=self.winpos)
        self.winpos += 50
        vis.add_geometry(pc.get_o3d())
        # Draw 1 meter axes (x=red, y=green, z=blue)
        axes = open3d.geometry.LineSet()
        axes.points = open3d.utility.Vector3dVector([[0,0,0], [1,0,0], [0,1,0], [0,0,1]])
        axes.lines = open3d.utility.Vector2iVector([[0,1], [0,2], [0,3]])
        axes.colors = open3d.utility.Vector3dVector([[1,0,0], [0,1,0], [0,0,1]])
        vis.add_geometry(axes)
        vis.run()
        vis.destroy_window()
        
    def align_pair(self, source, picked_id_source, target, picked_id_target, extended=False):
        assert(len(picked_id_source)>=3 and len(picked_id_target)>=3)
        assert(len(picked_id_source) == len(picked_id_target))
        corr = np.zeros((len(picked_id_source),2))
        corr[:,0] = picked_id_source
        corr[:,1] = picked_id_target

        p2p = open3d.registration.TransformationEstimationPointToPoint()
        trans_init = p2p.compute_transformation(source.get_o3d(), target.get_o3d(),
                 open3d.utility.Vector2iVector(corr))
        
        if not extended:
            return trans_init

        threshold = 0.01 # 3cm distance threshold
        reg_p2p = open3d.registration.registration_icp(source.get_o3d(), target.get_o3d(), threshold, trans_init,
                open3d.registration.TransformationEstimationPointToPoint())
        
        return reg_p2p.transformation
    
    def align_fine(self, source, target, threshold):
        trans_init = np.array([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]])
        reg_p2p = open3d.registration.registration_icp(source.get_o3d(), target.get_o3d(), threshold, trans_init,
                open3d.registration.TransformationEstimationPointToPoint())
        
        return reg_p2p.transformation

    def writeconfig(self):
        allcaminfo = ""
        for i in range(len(self.cameraserial)):
            serial = self.cameraserial[i]
            # Find matrix by applying what we found after the matrix read from the original config file (or the identity matrix)
            matrix = self.grabber.getmatrix(i)
            npMatrix = np.matrix(self.fine_matrix[i]) @ np.matrix(self.coarse_matrix[i]) @ np.matrix(matrix)
            matrix = npMatrix.tolist()
            matrixinfo = self.to_conf(matrix)
            caminfo = CONFIGCAMERA.format(serial=serial, matrixinfo=matrixinfo)
            allcaminfo += caminfo
        if self.near or self.far:
            distance = f'threshold_near="{self.near}" threshold_far="{self.far}"'
        else:
            distance = ''
        fileinfo = CONFIGFILE.format(cameras=allcaminfo, distance=distance)
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
    parser = argparse.ArgumentParser(description="Calibrate cwipc_realsense2 capturer")
    parser.add_argument("--clean", action="store_true", help="Remove old cameraconfig.xml and calibrate from scratch")
    parser.add_argument("--reuse", action="store_true", help="Reuse existing cameraconfig.xml")
    parser.add_argument("--noinspect", action="store_true", help="Don't inspect pointclouds after grabbing")
    parser.add_argument("--nograb", action="store", metavar="DIR", help="Don't use grabber, obtain .ply file and old config from DIR")
    parser.add_argument("--nocoarse", action="store_true", help="Skip coarse (manual) calibration step")
    parser.add_argument("--nofine", action="store_true", help="Skip fine (automatic) calibration step")
    parser.add_argument("--crossv3", action="store_true", help="Use version 3 calibration cross (with the LEDs)")
    parser.add_argument("--bbox", action="store", type=float, nargs=6, metavar="N", help="Set bounding box (in meters, xmin xmax etc) for fine calibration")
    parser.add_argument("--corr", action="store", type=float, metavar="D", help="Set fine calibration max corresponding point distance", default=0.01)
    parser.add_argument("--distance", type=float, action="store", required=True, metavar="D", help="Approximate distance between cameras and subject")
    args = parser.parse_args()
    distance = args.distance
    bbox = None
    if args.bbox:
        bbox = args.bbox
        assert len(bbox) == 6
        assert type(1.0*bbox[0]*bbox[1]*bbox[2]*bbox[3]*bbox[4]*bbox[5]) == float
    prog = Calibrator(distance, args.crossv3)
    if args.nograb:
        grabber = FileGrabber(args.nograb)
    else:
        grabber = LiveGrabber()
    try:
        prog.open(grabber, clean=args.clean, reuse=args.reuse)
        prog.grab(args.noinspect)
        if args.nocoarse: 
            prog.skip_coarse()
        else:
            prog.run_coarse()
        if args.nofine: 
            prog.skip_fine()
        else:
            prog.run_fine(bbox, args.corr)
        prog.save()
    finally:
        del prog
    
if __name__ == '__main__':
    main()
    
    
    
