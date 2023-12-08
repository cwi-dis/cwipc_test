ALL_MEASUREMENTS="
./genregtest/lootregtest0/lootregtest0.ply
./genregtest/lootregtest03/lootregtest03.ply
./genregtest/lootregtest003/lootregtest003.ply
./genregtest/genregtest0/genregtest0.ply 
./genregtest/genregtest03/genregtest03.ply 
./genregtest/genregtest003/genregtest003.ply 
./vrsmall/jack-sideways/jack-sideways.ply 
./vrsmall/jack-forward/jack-forward.ply 
./vrsmall/boxes/boxes.ply 
./vrbig/jack-sideways/jack-sideways.ply 
./vrbig/jack-forward/jack-forward.ply 
./vrbig/boxes/boxes.ply
"

set -x

for ply in $ALL_MEASUREMENTS; do
	python ../../cwipc/sandbox/registration_error_compute.py $ply
done