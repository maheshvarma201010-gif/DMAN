#!/bin/bash

echo "🚀 Starting Termux Setup for FAST MEDIA DOWNLOADER BOT..."

# Update packages
pkg update && pkg upgrade -y

# Install dependencies
pkg install python ffmpeg nodejs-lts git procps -y

# Install python requirements
pip install -r requirements.txt

# Create necessary folders
mkdir -p downloads sessions

echo "✅ Setup complete! Use 'python bot.py' to start the bot."
