# Latency measurements

Measurements were taken with VideoLat, [http://videolat.org](). MacBook was used for displaying the source QR code, an iPhone on the same wifi was used to capture. Both devices had the correct videoLat calibrations, so the numbers reported do not contain any latency caused by the test system (in other words: the numbers represent exactly what a human user would experience).

Measurements are avilable as PDF or `.videolat`, which can be opened in videolat for comparison or for exporting to CSV, etc.

## Measurements

- *m-pre1-realsense-viewer-3d-d435-usb2-imac* First measurement, really to test the setup.
- *m-pre2-realsense-viewer-3d-d435-usb3-arecibo* D435 on a production-class machine, using Intel software to show 3D data. Intended as "what we should aim for" for capturer.
- *m-pre3-pcl_align-d435* D435 using CWI capturer.
- *m-pre4-pcl_align-d415* D415 using CWI capturer.
- *m1-selfview-mesh* Testbed showing only a selfview of the CWI capturer (no other pointclouds shown, no compression or transmission going on). This uses the `mesh=true` option which I think is really for debug only.
- *m2-selfview-nomesh* Testbed showing only a selfview of the CWI capturer (no other pointclouds shown, no compression or transmission going on). This uses the `mesh=false` option which I think is intended for production.

## Auxiliary files

- *cameraconfig.xml* is a cwipc realsense2 camera configuration file that works well for putting the videolat screen about 50cm from a D435.
- *config-m1.json* is a Testbed config file that was used for m1 and shows the selfview in a decent enoughsize of videoLat to capture.