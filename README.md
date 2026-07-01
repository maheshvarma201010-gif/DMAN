# 🚀 FAST MEDIA DOWNLOADER BOT

An optimized Telegram bot for processing videos/audio with multi-language track selection.

## ⚙️ CORE FEATURES
- Fast, smooth, optimized video/audio processing.
- Uses FFmpeg for all processing (preset: ultrafast).
- Supports multi-language audio track selection.
- Admin-controlled access.
- MongoDB database support.
- Helper bots for speed scaling.

## 🛠️ DEPLOYMENT

### 🐳 Docker Deployment
1. Clone the repo.
2. Create a `config.env` file from the template.
3. Build and run:
```bash
docker build -t fast-media-bot .
docker run --env-file config.env fast-media-bot
```

### 📱 Termux Setup
1. Install Termux.
2. Update & install dependencies:
```bash
pkg update && pkg upgrade
pkg install python ffmpeg nodejs-lts
```
3. Clone repo and install requirements:
```bash
pip install -r requirements.txt
```
4. Configure environment variables and run:
```bash
python bot.py
```

## 🧾 COMMANDS
- `/start` → Admin only panel.
- `/language` → Set preferred audio language.
- `/settings` → Admin control panel.
- `/addhelper` → Add helper bot token.
- `/removehelper` → Remove helper bot.
- `/status` → Bot health & workers.

## 🌍 ENVIRONMENT VARIABLES
- `API_ID` & `API_HASH`
- `BOT_TOKEN`
- `MONGODB_URI`
- `AUTH_CHAT_ID`
- `HELPER_BOT_TOKENS` (space-separated list)
