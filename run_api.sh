#!/usr/bin/env bash
#
# Start Yoqu API (FastAPI)
#
PYTHONPATH=$PWD python ktxo/yoqu/api/main.py 2>&1 | egrep -v "MESA-INTEL|DevTools|\.cc|wrong ELF|-vkGetInstanceProcAddr"