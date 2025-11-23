#!/usr/bin/env bash
set -e  # Exit on error

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Building frontend..."
cd frontend
npm ci  # Clean install
npm run build
cd ..

echo "Build complete!"
ls -la frontend/dist  # Verify build output
