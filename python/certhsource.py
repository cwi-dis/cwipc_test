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
DEBUG_MESSAGES=False

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

class _RabbitmqReceiver:
    """Helper class to receive messages from a rabbitMQ channel and call a callback"""
    def __init__(self, rabbitmq, exchangeName, callback):
        self.rabbitmq = rabbitmq
        self.exchangeName = exchangeName
        self.callback = callback
        self.connection = None
        self.channel = None
        self.thread = None
        self._init_rabbitmq()
        self._start_rabbitmq()

    def _init_rabbitmq(self):
        parameters = pika.URLParameters(self.rabbitmq)

        self.connection = pika.BlockingConnection(parameters)
        if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: connection={self.connection}", flush=True, file=sys.stderr)
        self.channel = self.connection.channel()
        self.channel.queue_declare(self.exchangeName)
        self.channel.queue_bind(self.exchangeName, self.exchangeName)
        self.channel.basic_consume(self.exchangeName, self._on_data)
        if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: datachannel={self.channel}", flush=True, file=sys.stderr)

    def _start_rabbitmq(self):
        self.thread = threading.Thread(target=self._run_rabbitmq, args=())
        self.thread.start()
        if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: datathread={self.thread}", flush=True, file=sys.stderr)
        
    def stop(self):
        if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: stopping rabbitmq connection", flush=True, file=sys.stderr)
        if self.thread:
            if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: close channel", flush=True, file=sys.stderr)
            try:
                self.channel.close()
            except pika.exceptions.StreamLostError:
                pass
            except pika.exceptions.ChannelWrongStateError:
                pass
            except:
                print(f"cwipc_certh: {self.exchangeName}: ignoring exception during channel.close()")
            self.chanel = None
            if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: join data consumer thread", flush=True, file=sys.stderr)
            self.thread.join()
            self.thread = None
        if self.channel:
            if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: stop data channel", flush=True, file=sys.stderr)
            try:
                self.channel.close()
            except pika.exceptions.ChannelWrongStateError:
                pass
            self.channel = None
        if self.connection:
            if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: close data connection", flush=True, file=sys.stderr)
            try:
                self.connection.close()
            except pika.exceptions.ConnectionWrongStateError:
                pass                
            self.connection = None
        if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: stopped rabbitmq connection", flush=True, file=sys.stderr)
            
    def _run_rabbitmq(self):
        if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: start consuming data", flush=True, file=sys.stderr)
        try:
            self.channel.start_consuming()
        except pika.exceptions.StreamLostError:
            print(f"cwipc_certh: {self.exchangeName}: lost rabbitmq data stream", flush=True, file=sys.stderr)
            self.callback(None)
        if DEBUG: print(f"cwipc_certh: DEBUG: {self.exchangeName}: stopped consuming data", flush=True, file=sys.stderr)   
             
    def _on_data(self, channel, method_frame, header_frame, body):
        if DEBUG_MESSAGES:
            print(f"cwipc_certh: DEBUG: {self.exchangeName}: _on_data({channel}, ...):", flush=True, file=sys.stderr)
            print(method_frame.delivery_tag, flush=True, file=sys.stderr)
            print(body, flush=True, file=sys.stderr)
            print("", flush=True, file=sys.stderr)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        self.callback(body)
             
class cwipc_certh:
    def __init__(self, rabbitmq, dataExchange, metaDataExchange):
        self.handle = None
        self.dataReceiver = _RabbitmqReceiver(rabbitmq, dataExchange, self._dataCallback)
        self.metaDataReceiver = _RabbitmqReceiver(rabbitmq, metaDataExchange, self._metaDataCallback)
        self.queue = queue.Queue()
                
    def __del__(self):
        self.free()

    def _dataCallback(self, data):
        if data == None:
            return
        if DEBUG: print(f"cwipc_certh: got data, {len(data)} bytes")
        
    def _metaDataCallback(self, data):
        if data == None:
            return
        if DEBUG: print(f"cwipc_certh: got metadata, {len(data)} bytes")
        
    def free(self):
        if self.handle:
            assert self.dll
#            self.dll.sub_destroy(self.handle)
            self.handle = None
        if self.dataReceiver: self.dataReceiver.stop()
        self.dataReceiver = None
        if self.metaDataReceiver: self.metaDataReceiver.stop()
        self.metaDataReceiver = None
        self.queue.put(None)
            
    def eof(self):
        return self.dataReceiver == None
        
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
