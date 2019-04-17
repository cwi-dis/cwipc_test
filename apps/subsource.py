import ctypes
import ctypes.util
import time

_signals_unity_bridge_dll_reference = None

class sub_handle_p(ctypes.c_void_p):
    pass
    
class FrameInfo(ctypes.Structure):
    _fields_ = [
        ("timestamp", ctypes.c_longlong)
    ]
    
def _signals_unity_bridge_dll(libname=None):
    global _signals_unity_bridge_dll_reference
    if _signals_unity_bridge_dll_reference: return _signals_unity_bridge_dll_reference
    
    if libname == None:
        libname = ctypes.util.find_library('signals-unity-bridge')
        if not libname:
            raise RuntimeError('Dynamic library signals-unity-bridge not found')
    assert libname
    _signals_unity_bridge_dll_reference = ctypes.cdll.LoadLibrary(libname)
    
    _signals_unity_bridge_dll_reference.sub_create.argtypes = [ctypes.c_char_p]
    _signals_unity_bridge_dll_reference.sub_create.restype = sub_handle_p
    
    _signals_unity_bridge_dll_reference.sub_destroy.argtypes = [sub_handle_p]
    _signals_unity_bridge_dll_reference.sub_destroy.restype = None
    
    _signals_unity_bridge_dll_reference.sub_get_stream_count.argtypes = [sub_handle_p]
    _signals_unity_bridge_dll_reference.sub_get_stream_count.restype = ctypes.c_int
    
    _signals_unity_bridge_dll_reference.sub_play.argtypes = [sub_handle_p, ctypes.c_char_p]
    _signals_unity_bridge_dll_reference.sub_play.restype = ctypes.c_bool
    
    _signals_unity_bridge_dll_reference.sub_grab_frame.argtypes = [sub_handle_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
    _signals_unity_bridge_dll_reference.sub_grab_frame.restype = ctypes.c_size_t
    
    return _signals_unity_bridge_dll_reference
 
class CpcSubSource:
    def __init__(self, url):
        self.url = url
        self.dll = None
        self.handle = None
        self.dll = _signals_unity_bridge_dll()
        self.handle = self.dll.sub_create("SUBsource".encode('utf8'))
        assert self.handle
        ok = self.dll.sub_play(self.handle, url.encode('utf8'))
        assert ok
        nstreams = self.dll.sub_get_stream_count(self.handle)
        print('SUBsource: number of streams:', nstreams)
        assert nstreams >= 1
        self.streamIndex = 0
        
    def __del__(self):
        self.free()
        
    def free(self):
        if self.handle:
            assert self.dll
            self.dll.sub_destroy(self.handle)
            self.handle = None
            
    def read_cpc(self):
        assert self.handle
        assert self.dll
        while True:
            length = self.dll.sub_grab_frame(self.handle, self.streamIndex, None, 0, None)
            print('xxxjack read_cpc: length:', length)
            if length: break
            time.sleep(1)
        rv = bytearray(length)
        ptr_char = (ctypes.c_char * length).from_buffer(rv)
        ptr = ctypes.cast(ptr_char, ctypes.c_void_p)
        length2 = self.dll.sub_grab_frame(self.handle, self.streamIndex, ptr, length, None)
        assert length2 == length
        return rv
        
