import sys
import os
import time
import socket
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
    if len(sys.argv) > 2 or (len(sys.argv) > 1 and sys.argv[1] in {'-h', '--help'}):
        print('Usage: %s [port]' % sys.argv[0])
        sys.exit(1)
    port = 4303
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    srv = SourceServer(port)
    srv.serve()
    
if __name__ == '__main__':
    main()
    
    
    