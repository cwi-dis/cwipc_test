# Component (or Module?) Architecture

There is a roadmap listing the functional requirements in [VRTogether -> WP4 -> 2 Pilot Deployment -> Pilot 2 Roadmap](https://docs.google.com/spreadsheets/d/1LWXo9TT2WHDSOZ21KV1FCVoJb1rjeFO38Yn5qlGxMkU/edit#gid=0). That document breaks down the required functionality for the native pipeline (among many other things). But it does not provide an architectural component breakdown, i.e. it does not say which bits of the functionality have to be implemented _how_, and _where_, and _how they communicate_.

There is another document, [VRTogether -> WP2 -> Component Architecture -> Component Architecture Diagram](https://drive.google.com/drive/folders/12zn_7XrHzwREYAY4k3SUIFCusUBd0FHt?ths=true), that is indeed a component diagram, but it is too abstract. Specifically, it does not show anything about _how_ and _where_.

Those points are important: for example, a capturer that is implemented as a process on a standalone machine could communicate with an orchestration server over a socket connection. But a capturer that is implemented as a plugin DLL cannot work that way (because it has no thread of control) and will need another mechanism to communicate with the orchestrator. Actually: _some other component_ will have to obtain relevant parameters from a DLL-based capturer (using the capturer API) and communicate those parameters to the orchestrator service.

This document tries to outline which components need to be implemented where, and how, and the information that needs to flow between them.

## Minimum Viable Pipeline

The Minimum Viable Pipeline (from the Pilot 2 Roadmap document, id 48 in that document) is pretty much what some of us have working as of end of April 2019. It could also be considered the Pilot 1 pipeline re-implemented using Pilot 2 functionality.

![Minimum Viable Pipeline Diagram](component-architecture-diagrams/Minimum viable pipeline.pdf)

The pointcloud source consists of a machine running 2 processes: 

- *pcl2dash* which grabs pointclouds using *cwipc_realsense2*, encodes them using *cwipc_codec* and deposits the resulting MPD files and media segments into a directory. 
- The content of that directory is served by the *GPAC nodejs dash server*

The pointcloud sink consists of a machine with 1 process: *Testbed*. It uses the *Signals Unity Bridge* to obtain compressed pointcloud data (from the dash server in the sender), passes these through *cwipc_codec* for decompressing and then renders them.

It should be possible to create a full-duplex experience between 2 users by running both the 2 sender processes and the 1 receiver process on a single machine.

### Missing Functionality

#### Self view

> This point is open to discussion.

While not needed for the minimum viable pipeline this *will* be needed eventually, and in my opinion having *pcl2dash* in a different process (hence address space) than the renderer precludes self view. I do not see a viable solution to this except moving the *pcl2dash* functionality into the same address space as the renderer.

#### Firewall traversal and upstream bandwidth

Again, not needed for the minimum viable pipeline, but needed in the future. Currently the *dash server* shares a file system with *pcl2dash*. This creates two problems:

- The source machine must have ports open on publicly visible static IP addresses, i.e. it cannot be behind a NAT (at least not with major headaches, especially for the multi-user case).
- The source machine will need ample upstream bandwidth (for the multi-user case) to stream to **all** other participants. 
 
#### Orchestration

The orchestration service is missing in this pipeline, and its functionality is implemented by manually copying configuration parameters between files on the different machines. Specifically:

- The IP address of the source PC (actually the URL for the dash MPD file created by pcl2dash and served by the dash server) has to be entered into the `config.json` of *Testbed* on the destination machine.
- The position, orientation, size and point size of the source pointcloud in the destination scene have to be entered manually in various variables deep inside *Testbed*.
- The position (and maybe more, I am not sure) of the viewpoint of the destination viewer has to be manually entered in variables in *Testbed*.

## Self View Pipeline

A second pipeline that works as of late April 2019 is the self view pipeline:

![Self View Pipeline Diagram](component-architecture-diagrams/Camera Test.pdf)

The only reason to show it here is really to demonstrate that the *cwipc_realsense2* capturer component can function within the *Testbed* architecture.

## Multiuser pipeline

The next milestone according to the Pilot 2 roadmap is the 4-user session, with a single camera per user.

> Looking at the way the various components are progressing I can imagine another milestone: a 2-user multi-camera session. I have not drawn a diagram for that, but maybe I should do so?

Here is an attempt at a modular architecture for the 4 user milestone, id 49 from the functional requirements:

![4 User Pipeline Diagram](component-architecture-diagrams/4user pipeline.pdf)

Note that this diagram **only** looks at pointclouds, because it reflects milestone 49 it ignores a number of vital things for the pilot (which is - as of this writing - only a bit more than a month away):

- TVMs
- Audio
- Multi-camera capture and tiling
- Pre-recorded content, scenes, etc
- Synchronization

But still, in this diagram I have made a number of - tentative - architectural choices that we need to get consensus on:

- I am assuming an orchestration endpoint. Some component will need to collect data about camera viewpoints (and eventually number of cameras, number of tiles, etc) and communicate that to the other participants. The orchestration endpoint will also need to communicate that information from the other participants to the renderer engine.
- The pointclouds grabbed using the *cwipc_realsense2* will need to go to two places: they need to be used for self view by the renderer and they will need to be encoded and transmitted. In the diagram I have made the *render loop* responsible but it could just as easily with the *dash loop* or a third *capture loop*. But whatever the solution: the pointclouds will need to go into two different directions.
- I'm presuming a *Unity Signals Bridge* that has the mechanics of uploading the segments and the modifications to the MPD file (if they are needed, I don't know) to the dash server. This may be over-engineering: maybe the *dash loop* and *USB* can simply be one DLL module that is called from *render loop* whenever a new pointcloud is available. But it will then need an API so that the *orchestration endpoint* can obtain the data it needs to share with the other participants in the session.
	- *Note*: for this milestone 49 one could assume that the information needed by the orchestration endpoint is static, but this is definitely not true when we move to the next milestone: the capturer module and the USB will have information about avaiable tiles, and this will govern how many streams are available originating from this participant, and the view points for each of these streams. This information is needed by the renderers for the other participants so that they can download only the needed tiles. 