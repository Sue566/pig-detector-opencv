#!/bin/bash
# Simple setup and training script for macOS
set -e
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
# install dependencies using Tsinghua mirror by default
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
VERSION=${VERSION:-v1}
python scripts/train.py --config config.yaml --version "$VERSION"
