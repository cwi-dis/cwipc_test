import sys
import os
import time
import socket
import argparse
import cwipc
import cwipc.codec
import cwipc.realsense2
    
class SourceServer:
    def __init__(self, port=4303):
        self.socket = socket.socket()
        self.socket.bind(('', port))
        self.socket.listen()
        self.grabber = cwipc.realsense2.cwipc_realsense2()
        
    def grab_cpc(self):
        pc = self.grabber.get()
        enc = cwipc.codec.cwipc_new_encoder()
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
            data = self.grab_cpc()
            s.sendall(data)
            s.close()
            
def main():
    parser = argparse.ArgumentParser(description="Start server to send compressed pointclouds to a cwipc_sourceserver_sink")
    parser.add_argument("--port", type=int, action="store", metavar="PORT", help="Port to connect to", default=4303)
    args = parser.parse_args()
    srv = SourceServer(args.port)
    srv.serve()
    
if __name__ == '__main__':
    main()
    
    
    
