# Paula

Captures of our mannequin (on 2025-08-06, in vrbig):

## `paula-miraco-orig.ply`

As exported from Miraco.

## `paula-miraco-resized.ply`

Converted with `--filter 'transform(0.157425, 806, -215.739532, 0.001)'`.

## `paula-captured.ply`

Captured with 4 Kinects, using `cameraconfig-captured.json`


## `paula-capturedwithfloor.ply`

Captured with 4 Kinects, using `cameraconfig-capturedwithfloor.json`

## `paula-miraco.ply`

Created by re-aligned `paula-miraco-resized.ply` to `paula-captured.ply`.


The command used was

```
cwipc_grab --playback paula-miraco-resized.ply --filter 'transform44([[0.8936720266977755, -0.09423216478760452, 0.43871472259012634, -0.16778378971473618], [0.03606211598653521, 0.9896211102407868, 0.1391027747975063, 0.005242338279640231], [-0.4472693064457517, -0.10849127746152591, 0.8877949145080197, 0.12690583674455294], [0.0, 0.0, 0.0, 1.0]])' .
```
followed by moving `pointcould-0001.ply` to its final name.


The details of the `cwipc_find_transform` run are in the `workdir-map-miraco-to-captured` directory.
