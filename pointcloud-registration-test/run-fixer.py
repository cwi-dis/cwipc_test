ALL_MEASUREMENTS="./genregtest/genregtest003/genregtest003.ply ./genregtest/genregtest03/genregtest03.ply ./vrsmall/jack-sideways/jack-sideways.ply ./vrsmall/jack-forward/jack-forward.ply ./vrsmall/boxes/boxes.ply ./vrbig/jack-sideways/jack-sideways.ply ./vrbig/jack-forward/jack-forward.ply ./vrbig/boxes/boxes.ply"

set -x

for ply in $ALL_MEASUREMENTS; do
	python ../../cwipc/sandbox/registration_error_fix.py $ply
done