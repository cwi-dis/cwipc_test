# cwipc_test

Repo for pointcloud tests.

## loot datasets

To create the loot datasets for testing:

- Download the original dataset from <https://jpeg.org/plenodb/pc/8ilabs/> into `../loot`.
	- You may have to edit the `Makefile` to show it where the dataset is.
- Install _cwipc\_util_ and _cwipc\_codec_.
- Clone the Deployment repo <https://baltig.viaccess-orca.com:8443/VRT/deployment-group/Deployment> into `../Deployment`.
	- Again, you may have to edit the `Makefile` if pathnames are different.
- Check that the _cwipc_ stuff is installed correctly and install dependencies (_numpy_, _open3d_):

  ```
  make deps
  ```
- Convert loot to smaller pointclouds, and compress those to _cwicpc_ files:

  ```
  make
  ```
 - Upload, possibly after editing `config/addReleaseToGitLab.json`:

   ```
   make release
   ```