import sys
import os
import time
import socket
import argparse
import open3d
import numpy as np
import cwipc
import cwipc.codec

    
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
        
class SinkClient:
    def __init__(self, hostname='localhost', port=4303):
        self.hostname = hostname
        self.port = port

    def read_cpc_from_socket(self):
        with socket.socket() as s:
            try:
                s.connect((self.hostname, self.port))
            except socket.error as err:
                print('connecting to {}:{}: {}'.format(self.hostname, self.port, err))
                sys.exit(1)
            rv = b''
            while True:
                data = s.recv(8192)
                if not data: break
                rv += data
            return rv
            
    def receiver_loop(self):
        while True:
            cpc = self.read_cpc_from_socket()
            pc = self.decompress(cpc)
            self.show(pc)
            
    def decompress(self, cpc):
        decomp = cwipc.codec.cwipc_new_decoder()
        decomp.feed(cpc)
        gotData = decomp.available(True)
        assert gotData
        pc = decomp.get()
        return pc
        
    def show(self, pc):
        o3dpc = cwipc_to_o3d(pc)
        self.draw_o3d(o3dpc)
            
    def draw_o3d(self, o3dpc):
        """Draw open3d pointcloud"""
        v = open3d.Visualizer()
        v.create_window()
        v.add_geometry(o3dpc)
        v.run()
        v.destroy_window()

    def run(self):
        self.receiver_loop()
        
def main():
    parser = argparse.ArgumentParser(description="Receive compressed pointclouds from a cwipc_sourceserver_source and display them")
    parser.add_argument("--hostname", action="store", metavar="HOSTNAME", help="Host or IP address to connect to", default="localhost")
    parser.add_argument("--port", type=int, action="store", metavar="PORT", help="Port to connect to", default=4303)
    args = parser.parse_args()
    clt = SinkClient(args.hostname, args.port)
    clt.run()
    
if __name__ == '__main__':
    main()
    
    
    
