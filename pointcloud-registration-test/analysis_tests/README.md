# Test data for `cwipc_analyze_registration`

## Loot data

Created with `cwipc_create_analysis`.
The Untiled loot, but converted to our coordinate system is `loot.ply`.

Each of the datasets has an `input.ply` with is that loot, converted to 4 cameras and with noise and transformations applied. For example, `loot-000-000-000-000-noise005` was created with

```
python -m cwipc.scripts.cwipc_create_analysis_test --ncamera 4 --noise 0.005 --move 0 loot.ply loot-000-000-000-000-noise005/input.ply
``` 

Generally, the graphs and pointclouds inside the folders were created with 

```
python -m cwipc.scripts.cwipc_find_transform --targettile 1 --sourcetile 2 --plot --dump input.ply input.ply
```

## captured data

The `captured-man-arms-raised.ply` and `captured-woman-arms-raised.ply` were taken from the "spirit dance" recordings (4 cameras each, in vrbig and vrsmall).

The `captured.ply` was captured in Tampere with 7 cameras.
