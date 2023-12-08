python ../../cwipc/sandbox/genregtest.py --single --distance 0 genregtest/genregtest0/genregtest0.ply
python ../../cwipc/sandbox/genregtest.py --single --distance 0.03 genregtest/genregtest03/genregtest03.ply
python ../../cwipc/sandbox/genregtest.py --single --distance 0.003 genregtest/genregtest003/genregtest003.ply
mkdir -p genregtest/lootregtest genregtest/lootregtest0 genregtest/lootregtest03 genregtest/lootregtest003
cwipc_grab --playback ../../loot/loot_vox10_1073.ply --filter 'transform(-168,0,-105,0.001815)' genregtest/lootregtest
python ../../cwipc/sandbox/genregtest.py --input genregtest/lootregtest/pointcloud-0001.ply --single --distance 0 genregtest/lootregtest0/lootregtest0.ply
python ../../cwipc/sandbox/genregtest.py --input genregtest/lootregtest/pointcloud-0001.ply --single --distance 0.03 genregtest/lootregtest03/lootregtest03.ply
python ../../cwipc/sandbox/genregtest.py --input genregtest/lootregtest/pointcloud-0001.ply --single --distance 0.003 genregtest/lootregtest003/lootregtest003.ply
