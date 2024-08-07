# Notes on samples

First: please leave the existing `loot-110K-4tiles`, `loot-150K-4tiles` and `Ulli1M` samples in place and do not change them.

They have been used for various papers and it is a good idea to keep them.

## Creating new samples

Let's presume we want to create a dataset of loot, compressed at various levels of detail.

Get a copy of the original 8i loot ply files, and put it in a folder `loot` next to the toplevel `cwipc_test` folder.

First we need to determine the parameters for converting loot to our coordinate system and scale:

```
cwipc_view --filter analyze --playback ../../loot
```

Let it run for a bit (you won't see anything because loot is going to be _very_ big), then press quit. You will get a suggested transform. Modify to your needs, and inspect the result:

```
cwipc_view --filter 'transform(-200,-300,0.0018)' --playback ../../loot
```

If that looks good create your output

```
cwipc_grab --filter 'transform(-200,0,-300,0.0018)' --playback ../../loot --compress --compress_param octree_bits=6 loot-compressed/depth6/
```

Check the results (note that frame rate is lost, currently):

```
cwipc_view --playback loot-compressed/depth6
```

Now repeat for other parameters.
