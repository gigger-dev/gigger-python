#!/bin/sh
# Exit immediately if a command exits with a non-zero status
set -e

# Set the current directory to the PYTHONPATH
export PYTHONPATH="$PWD:$PYTHONPATH"

# Define directories
SRC_DIR="lib"
ROOT_DIR=$(pwd)

# Navigate to the source directory and run Alembic migrations
if cd "$SRC_DIR"; then
    echo "Running Alembic migrations..."
    
    if ! alembic upgrade head; then
        echo "❌ Alembic migrations failed. Exiting..."
        exit 1
    fi
else
    echo "❌ Failed to navigate to $SRC_DIR. Exiting..."
    exit 1
fi

# Navigate back to the root directory
cd "$ROOT_DIR"

# Start the Uvicorn server
echo "🚀 Starting Uvicorn server..."
uvicorn main:fast_api_app --host 0.0.0.0 --port 8001 --reload