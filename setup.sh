#!/bin/bash

echo "🚀 Setting up FAST MEDIA DOWNLOADER BOT in Termux..."

# Update and upgrade
pkg update && pkg upgrade -y

# Install dependencies
pkg install python ffmpeg -y

# Install python requirements
pip install -r requirements.txt

echo "✅ Setup complete!"
echo "📝 Edit config.env with your credentials then run: python bot.py"
