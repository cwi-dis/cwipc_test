import sys
import os

dry_run=False
do_mkdir=False
do_clone=False
do_fetch=True
do_lfs_fetch=True
do_mirror=True
do_lfs_mirror=True

#Note: must end in /, if applicable

Old="ssh://git@baltig.viaccess-orca.com:8022/VRT/"
New="ssh://git@192.168.37.11:222/VRT-"

AllGroups=[
    "nativeclient-group",
    "deployment-group",
    "orchestration-group",
    "deliverymcu-group",
    "webclient-group"
]

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

if do_mkdir:
    for a in AllGroups:
        print('+ mkdir', a)
        if not dry_run:
            os.mkdir(a)
    
if do_clone:
    for a in All:
        cmd = f'git clone --mirror {Old}{a}.git {a}.git'
        print('+ ', cmd)
        if not dry_run:
            os.system(cmd)
            
if do_fetch:
    for a in All:
        cmd = f'(cd {a}.git && git fetch --all)'
        print('+ ', cmd)
        if not dry_run:
            os.system(cmd)

if do_lfs_fetch:
    for a in All:
        cmd = f'(cd {a}.git && git lfs fetch --all)'
        print('+ ', cmd)
        if not dry_run:
            os.system(cmd)

if do_mirror:
    for a in All:
        cmd = f'cd {a}.git && git push --mirror {New}{a})'
        print('+ ', cmd)
        if not dry_run:
            os.system(cmd)

if do_lfs_mirror:
    for a in All:
        cmd = f'(cd {a}.git && git lfs push --all {New}{a})'
        print('+ ', cmd)
        if not dry_run:
            os.system(cmd)

