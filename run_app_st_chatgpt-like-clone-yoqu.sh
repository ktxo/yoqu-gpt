#!/usr/bin/env bash

PYTHONPATH=$PWD streamlit run --server.address 0.0.0.0 --logger.level info ktxo/yoqu/appst/chatgpt-like-clone.py
