mkdir genregtest03 genregtest003
python ../../cwipc/sandbox/genregtest.py --distance 0.03 genregtest03/genregtest03.ply
python ../../cwipc/sandbox/genregtest.py --distance 0.003 genregtest03/genregtest003.ply
python ../../cwipc/sandbox/voxelize_curve.py genregtest03/genregtest03.ply
python ../../cwipc/sandbox/voxelize_curve.py genregtest003/genregtest003.ply
