import ctypes
import ctypes.util
import time
import os
import sys
import pika
import threading
import queue
import cwipc.util

_native_pcloud_receiver_dll_reference = None

DEBUG=True
DEBUG_MESSAGES=False
DEBUG_SAVE_FIRST_DATA='DEBUG_SAVE_FIRST_DATA' in os.environ and os.environ['DEBUG_SAVE_FIRST_DATA']
XXXJACK_KEEPIT=[]

def _native_pcloud_receiver_dll(libname=None):
    global _native_pcloud_receiver_dll_reference
    if _native_pcloud_receiver_dll_reference: return _native_pcloud_receiver_dll_reference
    if libname == None and 'NATIVE_PCLOUD_RECEIVER_DLL' in os.environ:
        libname = os.environ['NATIVE_PCLOUD_RECEIVER_DLL']
    if libname == None:
        libname = ctypes.util.find_library('native_pcloud_receiver')
        if not libname:
            raise RuntimeError('Dynamic library native_pcloud_receiver not found')
    assert libname
    # Signals library needs to be able to find some data files stored next to the DLL.
    # Tell it where they are.
    _native_pcloud_receiver_dll_reference = ctypes.cdll.LoadLibrary(libname)
    
    _native_pcloud_receiver_dll_reference.callColorizedPCloudFrameDLL.argstypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    _native_pcloud_receiver_dll_reference.callColorizedPCloudFrameDLL.restype = ctypes.c_void_p
    
    _native_pcloud_receiver_dll_reference.set_number_wrappers.argstypes = [ctypes.c_int]
    _native_pcloud_receiver_dll_reference.set_number_wrappers.restype = None
    
    _native_pcloud_receiver_dll_reference.received_metadata.argstypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    _native_pcloud_receiver_dll_reference.received_metadata.restype = ctypes.c_bool
    
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
    
    return _native_pcloud_receiver_dll_reference
    
class _RabbitmqReceiver:
    """Helper class to receive messages from a rabbitMQ channel and call a callback"""
    def __init__(self, rabbitmq, exchangeName, callback):
        self.rabbitmq = rabbitmq
        self.exchangeName = exchangeName
        self.callback = callback
        self.connection = None
        self.channel = None
        self.thread = None
        if DEBUG_SAVE_FIRST_DATA:
            self.did_save = False
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
        if DEBUG_SAVE_FIRST_DATA and not self.did_save:
            open(self.exchangeName + '.data', 'wb').write(body)
            print(f"cwipc_certh: saved message body to {self.exchangeName}.data", flush=True, file=sys.stderr)
            self.did_save = True
        self.callback(body)
             
class cwipc_certh:
    def __init__(self, rabbitmq, dataExchange, metaDataExchange):
        # Initialize captureer object
        self.handle = None
        self.dataReceiver = None
        self.metaDataReceiver = None
        self.pcl_id = 0
        self.receivedMetaData = False
        self.receivedMetaDataBuffer = None
        self.bbox = (-1.0, 1.0, -1.0, 0.5, -3.0, 1.0) # Random bounding box that works for camera on Jack's desk at home.
        self.queue = queue.Queue()
        # Load DLL early, so we get exceptions early
        _ = _native_pcloud_receiver_dll()
        _native_pcloud_receiver_dll().set_number_wrappers(1)
        # Create rabbitmq receivers
        self.dataReceiver = _RabbitmqReceiver(rabbitmq, dataExchange, self._dataCallback)
        self.metaDataReceiver = _RabbitmqReceiver(rabbitmq, metaDataExchange, self._metaDataCallback)
                
    def __del__(self):
        self.free()

    def _dataCallback(self, data):
        if data == None:
            if DEBUG: print("cwipc_certh: dataCallback got None argument", flush=True, file=sys.stderr)
            return
        if DEBUG: print(f"cwipc_certh: got data, {len(data)} bytes", flush=True, file=sys.stderr)
        if DEBUG: print(f"cwipc_certh: pushing raw data")
        self.queue.put(data)
        
    def _metaDataCallback(self, data):
        if data == None:
            if DEBUG: print("cwipc_certh: metaDataCallback got None argument", flush=True, file=sys.stderr)
            return
        self.receivedMetaDataBuffer = (ctypes.c_char * len(data)).from_buffer_copy(data)
        if DEBUG: print(f"cwipc_certh: got metadata, {len(self.receivedMetaDataBuffer)} bytes, address=0x{ctypes.addressof(self.receivedMetaDataBuffer):x}", flush=True, file=sys.stderr)
        self.receivedMetaData = _native_pcloud_receiver_dll().received_metadata(ctypes.cast(self.receivedMetaDataBuffer, ctypes.c_void_p), len(self.receivedMetaDataBuffer), self.pcl_id)
        
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
        self.keep_metadata_object = None
            
    def eof(self):
        return self.dataReceiver == None
        
    def available(self, wait):
        if wait:
            item = self.queue.get()
            self.queue.put(item)
            return True
        return not self.queue.empty()
        
    def get(self):
        data = self.queue.get()
        if data == None:
            if DEBUG: print("cwipc_certh: queue.get() got None result", flush=True, file=sys.stderr)
            return
        if not self.receivedMetaData: 
            if DEBUG: print(f"cwipc_certh: received raw pointcloud but no metaData yet", flush=True, file=sys.stderr)
            return
        dataPointer = (ctypes.c_char * len(data)).from_buffer_copy(data)
        if DEBUG: print(f"cwipc_certh: got raw pointcloud data, {len(dataPointer)} bytes, address=0x{ctypes.addressof(dataPointer):x}", flush=True, file=sys.stderr)
        try:
            certhPC = _native_pcloud_receiver_dll().callColorizedPCloudFrameDLL(ctypes.cast(dataPointer, ctypes.c_void_p), len(dataPointer), self.pcl_id)
        except Exception as e:
            print(f"cwipc_certh: Exception in callColorizedPCloudFrameDLL: {e}", flush=True, file=sys.stderr)
            return None
        if DEBUG: print(f"cwipc_certh: got certPC")
        return cwipc.util.cwipc_from_certh(certhPC, 0, self.bbox)

