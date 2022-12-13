#!/bin/bash
build_venv=false
use_venv=false
if $build_venv; then
	python3 -m venv .venv
	. .venv/bin/activate
	pip install /usr/local/share/cwipc/python/cwipc_util-7.3.7+5d45b03-py3-none-any.whl
fi
if $use_venv; then
	. .venv/bin/activate
fi
python ../../scripts/convert_image.py --pointsize 0.001 PM5644.svg.png ply/testpattern_000.ply
python ../../scripts/convert_image.py --pointsize 0.001 PM5644.svg.png cwipcdump/testpattern_000.cwipcdump

