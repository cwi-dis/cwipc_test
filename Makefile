#
# This is the Ply directory in the downloaded loot dataset
#
LOOT_PLY_DIR=../loot/loot/Ply
LONGDRESS_PLY_DIR=../longdress/longdress/Ply
REDANDBLACK_PLY_DIR=../redandblack/redandblack/Ply
SOLDIER_PLY_DIR=../soldier/soldier/Ply
#
# This is where the addRelease script lives
#
ADD_RELEASE=../Deployment/scripts/addReleaseToGitLab

#
# Directory where compressed pointclouds are stored
#

COMPRESSED_DIRS_LOOT=lootCwicpc lootCwicpc[0-9] lootCwicpc-low lootCwicpc[0-9]-low
COMPRESSED_DIRS_LONGDRESS=longdressCwicpc longdressCwicpc[0-9] longdressCwicpc-low longdressCwicpc[0-9]-low
COMPRESSED_DIRS_REDANDBLACK=redandblackCwicpc redandblackCwicpc[0-9] redandblackCwicpc-low redandblackCwicpc[0-9]-low
COMPRESSED_DIRS_SOLDIER=soldierCwicpc soldierCwicpc[0-9] soldierCwicpc-low soldierCwicpc[0-9]-low
COMPRESSED_DIRS=${COMPRESSED_DIRS_LOOT} ${COMPRESSED_DIRS_LONGDRESS} ${COMPRESSED_DIRS_REDANDBLACK} ${COMPRESSED_DIRS_SOLDIER}

#
# Zipfiles. Note that only those in ZIPFILES are part of a distribution.
#
ZIPFILES_LOOT=deliverables/loot-ply.zip deliverables/loot-cwicpc.zip
ZIPFILES_LONGDRESS=deliverables/longdress-ply.zip deliverables/longdress-cwicpc.zip
ZIPFILES_REDANDBLACK=deliverables/redandblack-ply.zip deliverables/redandblack-cwicpc.zip
ZIPFILES_SOLDIER=deliverables/soldier-ply.zip deliverables/soldier-cwicpc.zip
ZIPFILES=${ZIPFILES_LOOT} ${ZIPFILES_LONGDRESS} ${ZIPFILES_REDANDBLACK}

all: ${ZIPFILES}

release: ${ZIPFILES}
	python3 ${ADD_RELEASE} --curdir
	
prereq:
	python3 -m pip install -r scripts/requirements.txt
	# Assert cwipc is in PYTHONPATH
	python3 -c 'import cwipc'
	
lootPly ${COMPRESSED_DIRS_LOOT}:
	python3 scripts/convert_loot.py ${LOOT_PLY_DIR} lootPly lootCwicpc
	
longdressPly ${COMPRESSED_DIRS_LONGDRESS}:
	python3 scripts/convert_loot.py ${LONGDRESS_PLY_DIR} longdressPly longdressCwicpc
	
redandblackPly ${COMPRESSED_DIRS_REDANDBLACK}:
	python3 scripts/convert_loot.py ${REDANDBLACK_PLY_DIR} redandblackPly redandblackCwicpc
	
soldierPly ${COMPRESSED_DIRS_SOLDIER}:
	python3 scripts/convert_loot.py ${SOLDIER_PLY_DIR} soldierPly soldierCwicpc
	

deliverables/loot-ply.zip: lootPly
	mkdir -p deliverables
	zip -r deliverables/loot-ply.zip lootPly
	
deliverables/longdress-ply.zip: longdressPly
	mkdir -p deliverables
	zip -r deliverables/longdress-ply.zip longdressPly
	
deliverables/redandblack-ply.zip: redandblackPly
	mkdir -p deliverables
	zip -r deliverables/redandblack-ply.zip redandblackPly
	
deliverables/soldier-ply.zip: soldierPly
	mkdir -p deliverables
	zip -r deliverables/soldier-ply.zip soldierPly
	
deliverables/loot-cwicpc.zip: ${COMPRESSED_DIRS_LOOT}
	mkdir -p deliverables
	zip -r deliverables/loot-cwicpc.zip ${COMPRESSED_DIRS_LOOT}

deliverables/longdress-cwicpc.zip: ${COMPRESSED_DIRS_LONGDRESS}
	mkdir -p deliverables
	zip -r deliverables/longdress-cwicpc.zip ${COMPRESSED_DIRS_LONGDRESS}

deliverables/redandblack-cwicpc.zip: ${COMPRESSED_DIRS_REDANDBLACK}
	mkdir -p deliverables
	zip -r deliverables/redandblack-cwicpc.zip ${COMPRESSED_DIRS_REDANDBLACK}

deliverables/soldier-cwicpc.zip: ${COMPRESSED_DIRS_SOLDIER}
	mkdir -p deliverables
	zip -r deliverables/soldier-cwicpc.zip ${COMPRESSED_DIRS_SOLDIER}

#
# The *Dump targets are not for distribution, but for fast(er) playback of uncompressed pointclouds.
#
lootDump:
	python3 scripts/convert_ply2dump.py ${LOOT_PLY_DIR} lootDump

longdressDump:
	python3 scripts/convert_ply2dump.py ${LONGDRESS_PLY_DIR} longdressDump

redandblackDump:
	python3 scripts/convert_ply2dump.py ${REDANDBLACK_PLY_DIR} redandblackDump

soldierDump:
	python3 scripts/convert_ply2dump.py ${SOLDIER_PLY_DIR} soldierDump

clean:
	rm -rf lootPly longdressPly redandblackPly soldierPly ${COMPRESSED_DIRS}
