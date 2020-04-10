import ctypes
import ctypes.util
import cwipc.util

LIBNAME='C:/Users/VRTogether/VRTogether/certh/ColoredPointcloudDLL/ColoredPointCloud/Assets/Plugins/pcloud_receiver.dll'

class CerthCoordinate(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("w", ctypes.c_float),
    ]
    
class CerthPointCloud(ctypes.Structure):
    _fields_ = [
        ("numDevices", ctypes.c_int),
        ("vertexPtr", ctypes.c_void_p),
        ("normalPtr", ctypes.c_void_p),
        ("colorPtr", ctypes.c_void_p),
        ("deviceNames", ctypes.c_char_p),
        ("numVerticesPerCamera", ctypes.c_void_p),
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

class cwipc_certh:
    def __init__(self, bbox=None):
        self.bbox = bbox
        self.certhPC = None
        self.certhPCtimestamp = None
        
    def feed(self, certhPC, timestamp):
        self.certhPCtimestamp = timestamp
        self.certhPC = certhPC
        
    def get(self):
        if not self.certhPC: return None
        numDevices = self.certhPC.contents.numDevices
        numVerticesPerCamera = ctypes.cast(self.certhPC.contents.numVerticesPerCamera, ctypes.POINTER(ctypes.c_int*numDevices))
        vertexPtr = ctypes.cast(self.certhPC.contents.vertexPtr, ctypes.POINTER(ctypes.c_void_p*numDevices))
        colorPtr = ctypes.cast(self.certhPC.contents.colorPtr, ctypes.POINTER(ctypes.c_void_p*numDevices))
    
        all_point_data = []
        for camNum in range(numDevices):
            numVertices = numVerticesPerCamera.contents[camNum]
            print(f"camera[{camNum}]: {numVertices} vertices")
            print(f"camera[{camNum}]: vertexPtr=0x{vertexPtr.contents[camNum]:x}")
            print(f"camera[{camNum}]: colorPtr=0x{colorPtr.contents[camNum]:x}")
            vertexArrayType = CerthCoordinate * numVertices
            colorArrayType = ctypes.c_uint8 * (numVertices*3)
            vertexArray = ctypes.cast(vertexPtr.contents[camNum], ctypes.POINTER(vertexArrayType))
            colorArray = ctypes.cast(colorPtr.contents[camNum], ctypes.POINTER(colorArrayType))
            print(f"camera[{camNum}]: first point x={vertexArray.contents[0].x} y={vertexArray.contents[0].y} z={vertexArray.contents[0].z} w={vertexArray.contents[0].w}")
            print(f"camera[{camNum}]: first point r={colorArray.contents[0]} g={colorArray.contents[1]} b={colorArray.contents[2]}")

            for vertexNum in range(numVertices):
                x = vertexArray.contents[vertexNum].x
                y = vertexArray.contents[vertexNum].y
                z = vertexArray.contents[vertexNum].z
                # Note: colors are ordered BGR
                r = colorArray.contents[vertexNum*3 + 2]
                g = colorArray.contents[vertexNum*3 + 1]
                b = colorArray.contents[vertexNum*3 + 0]
                tile = (1 << camNum)
            
                if self.bbox:
                    if x < self.bbox[0] or x > self.bbox[1]: continue
                    if y < self.bbox[2] or x > self.bbox[3]: continue
                    if z < self.bbox[4] or x > self.bbox[5]: continue
                all_point_data.append((x, y, z, r, g, b, tile))
        pc = cwipc.util.cwipc_from_points(all_point_data, self.certhPCtimestamp)
        return pc

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
    print(f"\tnumDevices={pointcloudPtr.contents.numDevices}")
    print(f"\tvertexPtr=0x{pointcloudPtr.contents.vertexPtr:x}")
    print(f"\tnormalPtr=0x{pointcloudPtr.contents.normalPtr:x}")
    print(f"\tcolorPtr=0x{pointcloudPtr.contents.colorPtr:x}")
    print(f"\tdeviceNames={pointcloudPtr.contents.deviceNames}")
    print(f"\tnumVerticesPerCamera=0x{pointcloudPtr.contents.numVerticesPerCamera}")
    print(f"\tvertexChannels=0x{pointcloudPtr.contents.vertexChannels:x}")
    print(f"\tnormalChannels=0x{pointcloudPtr.contents.normalChannels:x}")
    print(f"\tcolorChannels=0x{pointcloudPtr.contents.colorChannels:x}")
    print(f"\tpclData=0x{pointcloudPtr.contents.pclData:x}")
    return pointcloudPtr

def dump_data(pointcloudPtr):    
    numDevices = pointcloudPtr.contents.numDevices
    numVerticesPerCamera = ctypes.cast(pointcloudPtr.contents.numVerticesPerCamera, ctypes.POINTER(ctypes.c_int*numDevices))
    vertexPtr = ctypes.cast(pointcloudPtr.contents.vertexPtr, ctypes.POINTER(ctypes.c_void_p*numDevices))
    colorPtr = ctypes.cast(pointcloudPtr.contents.colorPtr, ctypes.POINTER(ctypes.c_void_p*numDevices))
    
    all_point_data = []
    for camNum in range(numDevices):
        numVertices = numVerticesPerCamera.contents[camNum]
        print(f"camera[{camNum}]: {numVertices} vertices")
        print(f"camera[{camNum}]: vertexPtr=0x{vertexPtr.contents[camNum]:x}")
        print(f"camera[{camNum}]: colorPtr=0x{colorPtr.contents[camNum]:x}")
        vertexArrayType = CerthCoordinate * numVertices
        colorArrayType = ctypes.c_uint8 * (numVertices*3)
        vertexArray = ctypes.cast(vertexPtr.contents[camNum], ctypes.POINTER(vertexArrayType))
        colorArray = ctypes.cast(colorPtr.contents[camNum], ctypes.POINTER(colorArrayType))
        print(f"camera[{camNum}]: first point x={vertexArray.contents[0].x} y={vertexArray.contents[0].y} z={vertexArray.contents[0].z} w={vertexArray.contents[0].w}")
        print(f"camera[{camNum}]: first point r={colorArray.contents[0]} g={colorArray.contents[1]} b={colorArray.contents[2]}")

        for vertexNum in range(numVertices):
            x = vertexArray.contents[vertexNum].x
            y = vertexArray.contents[vertexNum].y
            z = vertexArray.contents[vertexNum].z
            # Note: colors are ordered BGR
            r = colorArray.contents[vertexNum*3 + 2]
            g = colorArray.contents[vertexNum*3 + 1]
            b = colorArray.contents[vertexNum*3 + 0]
            tile = (1 << camNum)
            
            all_point_data.append((x, y, z, r, g, b, tile))
        for p in all_point_data:
            print(p)

def show_data(certhPC):
    source = cwipc_certh()
    source.feed(certhPC, 0)
    pc = source.get()
    viewer = cwipc.util.cwipc_window("offline_certh")
    viewer.feed(pc, True)
    while viewer.interact("Press q to quit", "q", 1000):
        pass
    
test_setup()
test_metadata()
certhPC = test_data()
dump_data(certhPC)
show_data(certhPC)
