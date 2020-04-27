#!/bin/bash
#set -eu

export PCECHO_PATH=/d/Works/motion_spell/missions/201709_VRTogether/vo/cwipc_test/apps/pc_echo.py
export EVANESCENT_PATH=/d/Works/motion_spell/missions/201709_VRTogether/vo/Deployment/deliverables/evanescent/6/w64/evanescent.exe

export SIGNALS_SMD_PATH=/d/Works/motion_spell/missions/201709_VRTogether/vo/Deployment/deliverables/pcl2dash/42/w64_sub
export PATH=$PATH:/d/Works/motion_spell/missions/201709_VRTogether/tmp/cwipc_util_win1064_v2.6.0_stable/bin:'/c/Program Files/OpenNI2/Redist':'/c/Program Files (x86)/Intel RealSense SDK 2.0/bin/x64':'/c/Program Files (x86)/libjpeg-turbo64/bin':/c/Program\ Files/PCL\ 1.8.1/bin:$SIGNALS_SMD_PATH
export PYTHONPATH=/d/Works/motion_spell/missions/201709_VRTogether/tmp/cwipc_util_win1064_v2.6.0_stable/share/cwipc_util/python/

export RETRIES=10
export TIMEOUT=180

export RESULTS_PATH=scaling-measurements/results
mkdir -p $RESULTS_PATH

# fixed args
ARGS="--url http://127.0.0.1:9000/ --count 200 --retry 20"

# varying params
SEG_DURS="500 1000 2000 4000 8000"
declare -a TILES=("" "--tile")
declare -a OCTREE_BITS=('--octree_bits 6' '--octree_bits 11' '--octree_bits 6 --octree_bits 7' '--octree_bits 6 --octree_bits 7 --octree_bits 8' '--octree_bits 6 --octree_bits 7 --octree_bits 8 --octree_bits 9' '--octree_bits 6 --octree_bits 7 --octree_bits 8 --octree_bits 9 --octree_bits 10' '--octree_bits 6 --octree_bits 7 --octree_bits 8 --octree_bits 9 --octree_bits 10 --octree_bits 11')
PARALLELS=`seq 1 64 | xargs echo`

# run
for p in $PARALLELS ; do
  for i in "${!OCTREE_BITS[@]}" ; do
    for s in $SEG_DURS ; do
      for t in "${!TILES[@]}" ; do
        for (( r=0; r<$RETRIES; ++r)); do
          LOG_PATH="$RESULTS_PATH/parallel$p-octree$i-segdur$s-tile$t-run$r.log"
          if [ ! -f $LOG_PATH ] ; then
            # pc_echo sometimes fails
            while [ ! -f $LOG_PATH ] ; do
              "$EVANESCENT_PATH" > /dev/null &
              pid=$!
              LOCAL_CMD="$PCECHO_PATH $ARGS --parallel $p ${OCTREE_BITS[i]} --seg_dur $s ${TILES[t]}"
              echo Executing: time python3 $LOCAL_CMD
              timeout $TIMEOUT time python3 $LOCAL_CMD > "$LOG_PATH"
              retVal=$?
              if [ $retVal -ne 0 ]; then
                rm "$LOG_PATH"
                # # FIXME we used to retry until sucess or RETRIES exhaustion, but we faced
                #touch "$LOG_PATH".fail
              fi
              kill $pid
            done
          fi
        done
      done
    done
  done
done

echo DONE

