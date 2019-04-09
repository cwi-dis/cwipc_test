#
# This is the Ply directory in the downloaded loot dataset
LOOT_PLY_DIR=../loot/loot/Ply
#
# This is where the addRelease script lives
ADD_RELEASE=../Deployment/addReleaseToGitLab

all: deliverables/loot-ply.zip deliverables/loot-cwicpc.zip

release: deliverables/loot-ply.zip deliverables/loot-cwicpc.zip
	python3 ${ADD_RELEASE} --curdir
	
prereq:
	python3 -m pip install -r scripts/requirements.txt
	# Assert cwipc is in PYTHONPATH
	PYTHONPATH=/usr/local/share/cwipc_util/python python3 -c 'import cwipc'
	
lootPly lootCwicpc:
	PYTHONPATH=/usr/local/share/cwipc_util/python python3 scripts/convert_loot.py ${LOOT_PLY_DIR} lootPly lootCwicpc
	
deliverables/loot-ply.zip: lootPly
	zip -r deliverables/loot-ply.zip lootPly
	
deliverables/loot-cwicpc.zip: lootCwicpc
	zip -r deliverables/loot-cwicpc.zip lootCwicpc
