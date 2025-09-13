#!/bin/bash
set -e
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8092}
uvicorn scripts.api:app --host $HOST --port $PORT
