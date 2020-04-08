import ctypes
import ctypes.util
import threading

LIBNAME='C:/Users/VRTogether/VRTogether/certh/ColoredPointcloudDLL/ColoredPointCloud/Assets/Plugins/pcloud_receiver.dll'
USE_THREADS=False

class CerthPointCloud(ctypes.Structure):
    _fields_ = [
        ("numDevices", ctypes.c_int),
        ("vertexPtr", ctypes.c_void_p),
        ("normalPtr", ctypes.c_void_p),
        ("colorPtr", ctypes.c_void_p),
        ("deviceNames", ctypes.c_void_p),
        ("verticesPerCamera", ctypes.c_void_p),
        ("vertexChannels", ctypes.c_void_p),
        ("normalChannels", ctypes.c_void_p),
        ("colorChannels", ctypes.c_void_p),
        ("pclData", ctypes.c_void_p),
    ]

dll = ctypes.cdll.LoadLibrary(LIBNAME)

dll.callColorizedPCloudFrameDLL.argstypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
dll.callColorizedPCloudFrameDLL.restype = ctypes.POINTER(CerthPointCloud)

dll.set_number_wrappers.argstypes = [ctypes.c_int]
dll.set_number_wrappers.restype = None

dll.received_metadata.argstypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
dll.received_metadata.restype = ctypes.c_bool

pcl_id = 0

def test_setup():
    #
    # Setup DLL
    #
    dll.set_number_wrappers(1)

def test_metadata():
    #
    # Load metadata and feed to DLL
    #
    fp = open('VolumetricMetaData.data', 'rb')
    volumetricMetaData = fp.read()
    fp.close()
    print(f'volumetricMetaData: type={type(volumetricMetaData)}, size={len(volumetricMetaData)}', flush=True)
    volumetricMetaDataPtr = (ctypes.c_char * len(volumetricMetaData)).from_buffer_copy(volumetricMetaData)
    print(f'volumetricMetaDataPtr: address=0x{ctypes.addressof(volumetricMetaDataPtr):x}, size={len(volumetricMetaDataPtr)}', flush=True)
    ok = dll.received_metadata(ctypes.cast(volumetricMetaDataPtr, ctypes.c_void_p), len(volumetricMetaDataPtr), pcl_id)
    print(f'received_metadata returns {ok}')

def test_data():
    #
    # load data ald feed to DLL
    #
    fp = open('VolumetricData.data', 'rb')
    volumetricData = fp.read()
    fp.close()
    print(f'volumetricData: type={type(volumetricData)}, size={len(volumetricData)}', flush=True)
    volumetricDataPtr = (ctypes.c_char * len(volumetricData)).from_buffer_copy(volumetricData)
    print(f'volumetricData: address=0x{ctypes.addressof(volumetricDataPtr):x}, size={len(volumetricDataPtr)}', flush=True)
    pointcloudPtr = dll.callColorizedPCloudFrameDLL(ctypes.cast(volumetricDataPtr, ctypes.c_void_p), len(volumetricDataPtr), pcl_id)
    print(f'callColorizedPCloudFrameDLL returns 0x{pointcloudPtr}')

if not USE_THREADS:
    test_setup()
    test_metadata()
    test_data()
else:
    thread_setup = threading.Thread(target=test_setup, args=())
    thread_setup.start()
    thread_setup.join()

    thread_metadata = threading.Thread(target=test_metadata, args=())
    thread_metadata.start()
    thread_metadata.join()

    thread_data = threading.Thread(target=test_data, args=())
    thread_data.start()
    thread_data.join()

