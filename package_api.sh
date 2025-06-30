#!/bin/bash
# Package the API service into a tar.gz archive
set -e
PKG_NAME=pig-detector-api
TEMP_DIR=$(mktemp -d)
DEST="$TEMP_DIR/$PKG_NAME"
mkdir -p "$DEST"

cp -r scripts utils start_api.sh requirements.txt config.yaml "$DEST"
if [ -d models ]; then
  cp -r models "$DEST"
fi

# copy Dockerfile and build script for convenience
cp Dockerfile build_docker.sh "$DEST"

cd "$TEMP_DIR"
tar -czf "$OLDPWD/$PKG_NAME.tar.gz" "$PKG_NAME"
cd "$OLDPWD"
rm -rf "$TEMP_DIR"

echo "Package created: $PKG_NAME.tar.gz"
