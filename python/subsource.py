import ctypes
import ctypes.util
import time
import os

# If no data is available from the sub this is how long we sleep before trying again:
SLEEP_TIME=0.01
# If no data is available from the sub for this long we treat it as end-of-file:
EOF_TIME=10

SUB_API_VERSION = 0x20200327A

_signals_unity_bridge_dll_reference = None

class SubError(RuntimeError):
    pass
    
class sub_handle_p(ctypes.c_void_p):
    pass
    
class FrameInfo(ctypes.Structure):
    _fields_ = [
        ("timestamp", ctypes.c_longlong)
    ]
    
    
class streamDesc(ctypes.Structure):
    _fields_ = [
        ("MP4_4CC", ctypes.c_uint32),
        ("objectX", ctypes.c_uint32),
        ("objectY", ctypes.c_uint32),
        ("objectWidth", ctypes.c_uint32),
        ("objectHeight", ctypes.c_uint32),
        ("totalWidth", ctypes.c_uint32),
        ("totalHeight", ctypes.c_uint32),
    ]
        
def _signals_unity_bridge_dll(libname=None):
    global _signals_unity_bridge_dll_reference
    if _signals_unity_bridge_dll_reference: return _signals_unity_bridge_dll_reference
    
    if libname == None:
        libname = os.environ.get('VRTOGETHER_SUB_PATH')
        if not libname:
            libname = ctypes.util.find_library('signals-unity-bridge')
            if not libname:
                libname = ctypes.util.find_library('signals-unity-bridge.so')
            if not libname:
                raise SubError('Dynamic library signals-unity-bridge not found')
    assert libname
    # Signals library needs to be able to find some data files stored next to the DLL.
    # Tell it where they are.
    if os.path.isabs(libname) and not 'SIGNALS_SMD_PATH' in os.environ:
        libdirname = os.path.dirname(libname)
        os.putenv('SIGNALS_SMD_PATH', libdirname)
    _signals_unity_bridge_dll_reference = ctypes.cdll.LoadLibrary(libname)
    
    _signals_unity_bridge_dll_reference.sub_create.argtypes = [ctypes.c_char_p, ctypes.c_uint64]
    _signals_unity_bridge_dll_reference.sub_create.restype = sub_handle_p
    
    _signals_unity_bridge_dll_reference.sub_destroy.argtypes = [sub_handle_p]
    _signals_unity_bridge_dll_reference.sub_destroy.restype = None
    
    _signals_unity_bridge_dll_reference.sub_play.argtypes = [sub_handle_p, ctypes.c_char_p]
    _signals_unity_bridge_dll_reference.sub_play.restype = ctypes.c_bool
    
    _signals_unity_bridge_dll_reference.sub_get_stream_count.argtypes = [sub_handle_p]
    _signals_unity_bridge_dll_reference.sub_get_stream_count.restype = ctypes.c_int
    
    _signals_unity_bridge_dll_reference.sub_get_stream_info.argtypes = [sub_handle_p, ctypes.c_int, ctypes.POINTER(streamDesc)]
    _signals_unity_bridge_dll_reference.sub_get_stream_info.restype = ctypes.c_bool
    
    _signals_unity_bridge_dll_reference.sub_enable_stream.argtypes = [sub_handle_p, ctypes.c_int, ctypes.c_int]
    _signals_unity_bridge_dll_reference.sub_enable_stream.restype = ctypes.c_bool
    
    _signals_unity_bridge_dll_reference.sub_disable_stream.argtypes = [sub_handle_p, ctypes.c_int]
    _signals_unity_bridge_dll_reference.sub_disable_stream.restype = ctypes.c_bool
    
    _signals_unity_bridge_dll_reference.sub_grab_frame.argtypes = [sub_handle_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
    _signals_unity_bridge_dll_reference.sub_grab_frame.restype = ctypes.c_size_t
    
    return _signals_unity_bridge_dll_reference
 
class CpcSubSource:
    def __init__(self, url, streamIndex=0):
        self.url = url
        self.dll = None
        self.handle = None
        self.started = False
        self.streamIndex = streamIndex
        self.dll = _signals_unity_bridge_dll()
        assert self.dll
        self.handle = self.dll.sub_create("SUBsource".encode('utf8'), SUB_API_VERSION)
        if not self.handle:
            raise SubError("sub_create failed")
        
    def __del__(self):
        self.free()
        
    def free(self):
        if self.handle:
            assert self.dll
            self.dll.sub_destroy(self.handle)
            self.handle = None
            
    def start(self):
        assert self.handle
        assert self.dll
        ok = self.dll.sub_play(self.handle, self.url.encode('utf8'))
        if not ok: return False
        nstreams = self.dll.sub_get_stream_count(self.handle)
        assert nstreams > self.streamIndex
        self.started = True
        self.firstRead = True
        return True
        
    def count(self):
        assert self.handle
        assert self.dll
        assert self.started
        return self.dll.sub_get_stream_count(self.handle)
        
    def cpc_info_for_stream(self, num):
        assert self.handle
        assert self.dll
        assert self.started
        c_desc = streamDesc()
        ok = self.dll.sub_get_stream_info(self.handle, num, c_desc)
        if c_desc.objectWidth or c_desc.objectHeight or c_desc.totalWidth or c_desc.totalHeight:
            print(f"sub_get_stream_info({num}): MP4_4CC={c_desc.MP4_4CC},  objectX={c_desc.objectX},  objectY={c_desc.objectY},  objectWidth={c_desc.objectWidth},  objectHeight={c_desc.objectHeight},  totalWidth={c_desc.totalWidth},  totalHeight={c_desc.totalHeight}", file=sys.stdout)
            raise SubError(f"sub_get_stream_info({num}) returned unexpected information")
        return (c_desc.MP4_4CC, c_desc.objectX, c_desc.objectY)
    
    def read_cpc(self):
        assert self.handle
        assert self.dll
        assert self.started
        startTime = time.time()
        #
        # We loop until sub_grab_frame returns a length != 0
        #
        while time.time() < startTime + EOF_TIME:
            length = self.dll.sub_grab_frame(self.handle, self.streamIndex, None, 0, None)
            if length != 0:
                break
            time.sleep(SLEEP_TIME)
        if not length: 
            return None
        rv = bytearray(length)
        ptr_char = (ctypes.c_char * length).from_buffer(rv)
        ptr = ctypes.cast(ptr_char, ctypes.c_void_p)
        length2 = self.dll.sub_grab_frame(self.handle, self.streamIndex, ptr, length, None)
        assert length2 == length
        return rv
        
