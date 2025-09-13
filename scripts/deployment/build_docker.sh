#!/bin/bash
# Build Docker image for pig detector
set -e
IMAGE_NAME=pig-detector
# Use Tsinghua mirror by default for faster installs in China
PIP_INDEX_URL=${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}

docker build --build-arg PIP_INDEX_URL=$PIP_INDEX_URL -t $IMAGE_NAME .
echo "Docker image '$IMAGE_NAME' built successfully."
