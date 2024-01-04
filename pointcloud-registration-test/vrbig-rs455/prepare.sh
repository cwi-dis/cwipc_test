for fn in boxes jack-with-box; do
	cwipc_grab --playback captures/$fn.ply --filter 'colorize(1,"camera")' $fn/
	mv $fn/pointcloud-0001.ply $fn/$fn.ply
done

