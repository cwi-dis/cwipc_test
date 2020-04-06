import ctypes
import ctypes.util
import time
import os
import sys
import pika
import threading
import queue

_certh_dll_reference = None

DEBUG=True

# class streamDesc(ctypes.Structure):
#     _fields_ = [
#         ("MP4_4CC", ctypes.c_uint32),
#         ("objectX", ctypes.c_uint32),
#         ("objectY", ctypes.c_uint32),
#         ("objectWidth", ctypes.c_uint32),
#         ("objectHeight", ctypes.c_uint32),
#         ("totalWidth", ctypes.c_uint32),
#         ("totalHeight", ctypes.c_uint32),
#     ]
        
def _certh_dll(libname=None):
    global _certh_dll_reference
    if _certh_dll_reference: return _certh_dll_reference
    
    if libname == None:
        libname = ctypes.util.find_library('certh')
        if not libname:
            raise SubError('Dynamic library certh not found')
    assert libname
    # Signals library needs to be able to find some data files stored next to the DLL.
    # Tell it where they are.
    _certh_dll_reference = ctypes.cdll.LoadLibrary(libname)
    
#     _signals_unity_bridge_dll_reference.sub_create.argtypes = [ctypes.c_char_p, ctypes.c_uint64]
#     _signals_unity_bridge_dll_reference.sub_create.restype = sub_handle_p
#     
#     _signals_unity_bridge_dll_reference.sub_destroy.argtypes = [sub_handle_p]
#     _signals_unity_bridge_dll_reference.sub_destroy.restype = None
#     
#     _signals_unity_bridge_dll_reference.sub_play.argtypes = [sub_handle_p, ctypes.c_char_p]
#     _signals_unity_bridge_dll_reference.sub_play.restype = ctypes.c_bool
#     
#     _signals_unity_bridge_dll_reference.sub_get_stream_count.argtypes = [sub_handle_p]
#     _signals_unity_bridge_dll_reference.sub_get_stream_count.restype = ctypes.c_int
#     
#     _signals_unity_bridge_dll_reference.sub_get_stream_info.argtypes = [sub_handle_p, ctypes.c_int, ctypes.POINTER(streamDesc)]
#     _signals_unity_bridge_dll_reference.sub_get_stream_info.restype = ctypes.c_bool
#     
#     _signals_unity_bridge_dll_reference.sub_enable_stream.argtypes = [sub_handle_p, ctypes.c_int, ctypes.c_int]
#     _signals_unity_bridge_dll_reference.sub_enable_stream.restype = ctypes.c_bool
#     
#     _signals_unity_bridge_dll_reference.sub_disable_stream.argtypes = [sub_handle_p, ctypes.c_int]
#     _signals_unity_bridge_dll_reference.sub_disable_stream.restype = ctypes.c_bool
#     
#     _signals_unity_bridge_dll_reference.sub_grab_frame.argtypes = [sub_handle_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
#     _signals_unity_bridge_dll_reference.sub_grab_frame.restype = ctypes.c_size_t
    
    return _certh_dll_reference
 
class cwipc_certh:
    def __init__(self, rabbitmq, dataExchange, metaDataExchange):
        self.handle = None
        self.dataconnection = None
        self.datachannel = None
        self.datathread = None
        self.metadataconnection = None
        self.metadatachannel = None
        self.metadatathread = None
        self.queue = queue.Queue()
        self._init_rabbitmq(rabbitmq, dataExchange, metaDataExchange)
        self._start_rabbitmq()
                
    def __del__(self):
        self.free()

    def free(self):
        if self.handle:
            assert self.dll
#            self.dll.sub_destroy(self.handle)
            self.handle = None
        self._stop_rabbitmq()
        self.queue.put(None)

    def _init_rabbitmq(self, rabbitmq, dataExchange, metaDataExchange):
        parameters = pika.URLParameters(rabbitmq)

        self.dataconnection = pika.BlockingConnection(parameters)
        if DEBUG: print(f"cwipc_certh: DEBUG: dataconnection={self.dataconnection}", flush=True, file=sys.stderr)
        self.datachannel = self.dataconnection.channel()
        self.datachannel.queue_declare(dataExchange)
        self.datachannel.basic_consume(dataExchange, self._on_data)
        if DEBUG: print(f"cwipc_certh: DEBUG: datachannel={self.datachannel}", flush=True, file=sys.stderr)

        self.metadataconnection = pika.BlockingConnection(parameters)
        if DEBUG: print(f"cwipc_certh: DEBUG: metadataconnection={self.metadataconnection}", flush=True, file=sys.stderr)
        self.metadatachannel = self.metadataconnection.channel()
        self.metadatachannel.queue_declare(metaDataExchange)
        self.metadatachannel.basic_consume(metaDataExchange, self._on_metadata)
        if DEBUG: print(f"cwipc_certh: DEBUG: metadatachannel={self.metadatachannel}", flush=True, file=sys.stderr)
        
    def _start_rabbitmq(self):
        self.datathread = threading.Thread(target=self._run_rabbitmq_datachannel, args=())
        self.datathread.start()
        if DEBUG: print(f"cwipc_certh: DEBUG: datathread={self.datathread}", flush=True, file=sys.stderr)
        self.metadatathread = threading.Thread(target=self._run_rabbitmq_metadatachannel, args=())
        self.metadatathread.start()
        if DEBUG: print(f"cwipc_certh: DEBUG: metadatathread={self.metadatathread}", flush=True, file=sys.stderr)
        
    def _stop_rabbitmq(self):
        if DEBUG: print(f"cwipc_certh: DEBUG: stopping rabbitmq connection", flush=True, file=sys.stderr)
        if self.datathread:
            if DEBUG: print(f"cwipc_certh: DEBUG: stop consuming data", flush=True, file=sys.stderr)
            try:
                self.datachannel.stop_consuming()
            except pika.exceptions.StreamLostError:
                pass
            if DEBUG: print(f"cwipc_certh: DEBUG: join data consumer thread", flush=True, file=sys.stderr)
            self.datathread.join()
            self.datathread = None
        if self.metadatathread:
            if DEBUG: print(f"cwipc_certh: DEBUG: stop consuming metadata", flush=True, file=sys.stderr)
            try:
                self.metadatachannel.stop_consuming()
            except pika.exceptions.StreamLostError:
                pass
            if DEBUG: print(f"cwipc_certh: DEBUG: join metadata consumer thread", flush=True, file=sys.stderr)
            self.metadatathread.join()
            self.metadatathread = None
        if self.datachannel:
            if DEBUG: print(f"cwipc_certh: DEBUG: stop data channel", flush=True, file=sys.stderr)
            try:
                self.datachannel.close()
            except pika.exceptions.ChannelWrongStateError:
                pass
            self.datachannel = None
        if self.metadatachannel:
            if DEBUG: print(f"cwipc_certh: DEBUG: stop metadata channel", flush=True, file=sys.stderr)
            try:
                self.metadatachannel.close()
            except pika.exceptions.ChannelWrongStateError:
                pass
            self.metadatachannel = None
        if self.dataconnection:
            if DEBUG: print(f"cwipc_certh: DEBUG: close data connection", flush=True, file=sys.stderr)
            try:
                self.dataconnection.close()
            except pika.exceptions.ConnectionWrongStateError:
                pass                
            self.dataconnection = None
        if self.metadataconnection:
            if DEBUG: print(f"cwipc_certh: DEBUG: close metadata connection", flush=True, file=sys.stderr)
            try:
                self.metadataconnection.close()
            except pika.exceptions.ConnectionWrongStateError:
                pass                
            self.metadataconnection = None
        if DEBUG: print(f"cwipc_certh: DEBUG: stopped rabbitmq connection", flush=True, file=sys.stderr)
            
    def _run_rabbitmq_datachannel(self):
        if DEBUG: print(f"cwipc_certh: DEBUG: start consuming data", flush=True, file=sys.stderr)
        try:
            self.datachannel.start_consuming()
        except pika.exceptions.StreamLostError:
            print("cwipc_certh: lost rabbitmq data stream")
            self.queue.put(None)
        if DEBUG: print(f"cwipc_certh: DEBUG: stopped consuming data", flush=True, file=sys.stderr)
            
    def _run_rabbitmq_metadatachannel(self):
        if DEBUG: print(f"cwipc_certh: DEBUG: start consuming metadata", flush=True, file=sys.stderr)
        try:
            self.metadatachannel.start_consuming()
        except pika.exceptions.StreamLostError:
            print("cwipc_certh: lost rabbitmq metadata stream")
            self.queue.put(None)
        if DEBUG: print(f"cwipc_certh: DEBUG: stopped consuming metadata", flush=True, file=sys.stderr)
            
    def _on_data(self, channel, method_frame, header_frame, body):
        if DEBUG:
            print(f"cwipc_certh: DEBUG: _on_data({channel}, ...):", flush=True, file=sys.stderr)
            print(method_frame.delivery_tag, flush=True, file=sys.stderr)
            print(body, flush=True, file=sys.stderr)
            print("", flush=True, file=sys.stderr)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def _on_metadata(self, channel, method_frame, header_frame, body):
        if DEBUG:
            print(f"cwipc_certh: DEBUG: _on_metadata({channel}, ...):", flush=True, file=sys.stderr)
            print(method_frame.delivery_tag, flush=True, file=sys.stderr)
            print(body, flush=True, file=sys.stderr)
            print("", flush=True, file=sys.stderr)
        print(method_frame.delivery_tag)
        print(body)
        print()
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

            
    def eof(self):
        return self.dataconnection == None
        
    def available(self, wait):
        if wait:
            item = self.queue.get()
            self.queue.put(item)
            return True
        return not self.queue.empty()
        
    def get(self):
        return self.queue.get()
            
#     def start(self):
#         assert self.handle
#         assert self.dll
#         ok = self.dll.sub_play(self.handle, self.url.encode('utf8'))
#         if not ok: return False
#         nstreams = self.dll.sub_get_stream_count(self.handle)
#         assert nstreams > self.streamIndex
#         self.started = True
#         self.firstRead = True
#         return True
#         
#     def count(self):
#         assert self.handle
#         assert self.dll
#         assert self.started
#         return self.dll.sub_get_stream_count(self.handle)
#         
#     def cpc_info_for_stream(self, num):
#         assert self.handle
#         assert self.dll
#         assert self.started
#         c_desc = streamDesc()
#         ok = self.dll.sub_get_stream_info(self.handle, num, c_desc)
#         if c_desc.objectWidth or c_desc.objectHeight or c_desc.totalWidth or c_desc.totalHeight:
#             print(f"sub_get_stream_info({num}): MP4_4CC={c_desc.MP4_4CC},  objectX={c_desc.objectX},  objectY={c_desc.objectY},  objectWidth={c_desc.objectWidth},  objectHeight={c_desc.objectHeight},  totalWidth={c_desc.totalWidth},  totalHeight={c_desc.totalHeight}", file=sys.stdout)
#             raise SubError(f"sub_get_stream_info({num}) returned unexpected information")
#         return (c_desc.MP4_4CC, c_desc.objectX, c_desc.objectY)
#     
#     def read_cpc(self, streamIndex=None):
#         assert self.handle
#         assert self.dll
#         assert self.started
#         startTime = time.time()
#         if streamIndex == None:
#             streamIndex = self.streamIndex
#         #
#         # We loop until sub_grab_frame returns a length != 0
#         #
#         while time.time() < startTime + EOF_TIME:
#             length = self.dll.sub_grab_frame(self.handle, streamIndex, None, 0, None)
#             if length != 0:
#                 break
#             time.sleep(SLEEP_TIME)
#         if not length: 
#             return None
#         rv = bytearray(length)
#         ptr_char = (ctypes.c_char * length).from_buffer(rv)
#         ptr = ctypes.cast(ptr_char, ctypes.c_void_p)
#         length2 = self.dll.sub_grab_frame(self.handle, streamIndex, ptr, length, None)
#         if length2 != length:
#             raise SubError("read_cpc(stream={streamIndex}: was promised {length} bytes but got only {length2})")
#         return rv
#         
