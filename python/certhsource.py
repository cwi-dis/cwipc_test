import ctypes
import ctypes.util
import time
import os
import pika
import threading

_certh_dll_reference = None

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
        self.connection = None
        self.channel = None
        self.thread = None
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

    def _init_rabbitmq(self, rabbitmq, dataExchange, metaDataExchange):
        parameters = pika.URLParameters(rabbitmq)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(dataExchange)
        self.channel.basic_consume(dataExchange, self._on_data)
        self.channel.queue_declare(metaDataExchange)
        self.channel.basic_consume(metaDataExchange, self._on_metadata)
        
    def _start_rabbitmq(self):
        self.thread = threading.Thread(self._run_rabbitmq, ())
        
    def _stop_rabbitmq(self):
        if self.thread:
            self.channel.stop_consuming()
            self.thread.join()
            self.thread = None
        if self.channel:
            self.channel.close()
            self.channel = None
        if self.conection:
            self.connection.close()
            self.connection = None
            
    def _run_rabbitmq(self):
        self.channel.start_consuming()
            
    def _on_data(self, channel, method_frame, header_frame, body):
        print(f"_on_data({channel}, ...)")
        print(method_frame.delivery_tag)
        print(body)
        print()
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def _on_metadata(self, channel, method_frame, header_frame, body):
        print(f"_on_metadata({channel}, ...)")
        print(method_frame.delivery_tag)
        print(body)
        print()
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

            
    def eof(self):
        return False
        
    def available(self, wait):
        return True
        
    def get(self):
        return None
            
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
