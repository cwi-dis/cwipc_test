#
# This is the Ply directory in the downloaded loot dataset
LOOT_PLY_DIR=../loot/loot/Ply
LONGDRESS_PLY_DIR=../longdress/longdress/Ply
REDANDBLACK_PLY_DIR=../redandblack/redandblack/Ply
#
# This is where the addRelease script lives
ADD_RELEASE=../Deployment/addReleaseToGitLab
#
# Select one of the following depending on whether tiling is supported

COMPRESSED_DIRS_LOOT=lootCwicpc lootCwicpc[0-9] lootCwicpc-low lootCwicpc[0-9]-low
COMPRESSED_DIRS_LONGDRESS=longdressCwicpc longdressCwicpc[0-9] longdressCwicpc-low longdressCwicpc[0-9]-low
COMPRESSED_DIRS_REDANDBLACK=redandblackCwicpc redandblackCwicpc[0-9] redandblackCwicpc-low redandblackCwicpc[0-9]-low
COMPRESSED_DIRS=${COMPRESSED_DIRS_LOOT} ${COMPRESSED_DIRS_LONGDRESS} ${COMPRESSED_DIRS_REDANDBLACK}

ZIPFILES_LOOT=deliverables/loot-ply.zip deliverables/loot-cwicpc.zip
ZIPFILES_LONGDRESS=deliverables/longdress-ply.zip deliverables/longdress-cwicpc.zip
ZIPFILES_REDANDBLACK=deliverables/redandblack-ply.zip deliverables/redandblack-cwicpc.zip
ZIPFILES=${ZIPFILES_LOOT} ${ZIPFILES_LONGDRESS} ${ZIPFILES_REDANDBLACK}

all: ${ZIPFILES}

release: ${ZIPFILES}
	python3 ${ADD_RELEASE} --curdir
	
prereq:
	python3 -m pip install -r scripts/requirements.txt
	# Assert cwipc is in PYTHONPATH
	PYTHONPATH=/usr/local/share/cwipc_util/python python3 -c 'import cwipc'
	
lootPly ${COMPRESSED_DIRS_LOOT}:
	PYTHONPATH=/usr/local/share/cwipc_util/python python3 scripts/convert_loot.py ${LOOT_PLY_DIR} lootPly lootCwicpc
	
longdressPly ${COMPRESSED_DIRS_LONGDRESS}:
	PYTHONPATH=/usr/local/share/cwipc_util/python python3 scripts/convert_loot.py ${LONGDRESS_PLY_DIR} longdressPly longdressCwicpc
	
redandblackPly ${COMPRESSED_DIRS_REDANDBLACK}:
	PYTHONPATH=/usr/local/share/cwipc_util/python python3 scripts/convert_loot.py ${REDANDBLACK_PLY_DIR} redandblackPly redandblackCwicpc
	
deliverables/loot-ply.zip: lootPly
	mkdir -p deliverables
	zip -r deliverables/loot-ply.zip lootPly
	
deliverables/longdress-ply.zip: longdressPly
	mkdir -p deliverables
	zip -r deliverables/longdress-ply.zip longdressPly
	
deliverables/redandblack-ply.zip: redandblackPly
	mkdir -p deliverables
	zip -r deliverables/redandblack-ply.zip redandblackPly
	
deliverables/loot-cwicpc.zip: ${COMPRESSED_DIRS_LOOT}
	mkdir -p deliverables
	zip -r deliverables/loot-cwicpc.zip ${COMPRESSED_DIRS_LOOT}

deliverables/longdress-cwicpc.zip: ${COMPRESSED_DIRS_LONGDRESS}
	mkdir -p deliverables
	zip -r deliverables/longdress-cwicpc.zip ${COMPRESSED_DIRS_LONGDRESS}

deliverables/redandblack-cwicpc.zip: ${COMPRESSED_DIRS_REDANDBLACK}
	mkdir -p deliverables
	zip -r deliverables/redandblack-cwicpc.zip ${COMPRESSED_DIRS_REDANDBLACK}

clean:
	rm -rf lootPly longdressPly redandblackPly ${COMPRESSED_DIRS}
