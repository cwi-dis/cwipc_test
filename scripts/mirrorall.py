import sys
import os
All=[
	"nativeclient-group/VRTApp-MedicalExamination",
	"nativeclient-group/VRTApp-HoloMeet",
	"nativeclient-group/VRTApp-Museum",
	"nativeclient-group/VRTApp-Theatre",
	"nativeclient-group/VRTApp-Pilot3",
	"nativeclient-group/VRTApp-Pilot2",
	"nativeclient-group/VRTApp-Pilot1",
	"nativeclient-group/VRTApp-CWI_cake",
	"nativeclient-group/VRTApplication",
	"nativeclient-group/cwipc_kinect",
	"deployment-group/E2Etests",
	"nativeclient-group/Synchronizer",
	"nativeclient-group/TVM_components",
	"webclient/monitoringtools",
	"orchestration-group/Web_Orchestration",
	"nativeclient-group/cwipc_test",
	"nativeclient-group/thirdpartyinstallers",
	"nativeclient-group/Testbed",
	"nativeclient-group/cwipc_codec",
	"nativeclient-group/cwipc_realsense2",
	"nativeclient-group/SUB",
	"nativeclient-group/cwipc_util",
	"deployment-group/Deployment",
	"deliverymcu-group/DeliveryMCU",
	"nativeclient-group/Playout",
	"nativeclient-group/EncodingEncapsulation",
	"orchestration-group/Orchestration",
]

os.mkdir('nativeclient-group')
os.mkdir('deployment-group')
os.mkdir('webclient')
os.mkdir('orchestration-group')
os.mkdir('deliverymcu-group')
for a in All:
    print('+ ', a)
    os.system(f'git clone --mirror ssh://git@baltig.viaccess-orca.com:8022/VRT/{a}.git {a}.git')
    