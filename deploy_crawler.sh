#!/bin/bash

# Purpose: Simple deployment script for Modal crawler
# Description: Deploys the crawler to Modal with minimal setup

echo "🚀 Deploying Uptick Crawler to Modal..."

# Install Modal if not already installed
if ! command -v modal &> /dev/null; then
    echo "📦 Installing Modal..."
    pip install modal
fi

# Deploy the crawler
echo "🚀 Deploying crawler..."
modal deploy crawler/modal_deploy.py

echo "✅ Deployment complete!"
echo "🌐 View your app at: https://modal.com/apps/seth-1/uptick-crawler"

