for fn in boxes jack-forward jack-sideways; do
	cwipc_grab --playback $fn.ply --filter 'colorize(1,"camera")' $fn/
	mv $fn/pointcloud-0001.ply $fn/$fn.ply
done

