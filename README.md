# 🚀 FAST MEDIA LANGUAGE FILTER BOT

A production-grade Telegram bot built with Pyrogram and FFmpeg for maximum speed and stability. Automatically extracts preferred audio languages from videos.

## 🛠️ CORE FEATURES
- **Python 3.12+** & Latest Pyrogram
- **Multi-worker Queue System**: Independent per-user processing.
- **Helper Bot System**: Load-balanced downloading/uploading using multiple tokens and session strings.
- **FFmpeg Stream Copy**: Fast processing without re-encoding video.
- **Production Ready**: Docker, Docker-Compose, and Advanced Logging.

## 📱 TERMUX DEPLOYMENT GUIDE

1. **Update & Install Packages**:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python ffmpeg git clang rust libjpeg-turbo openssl wget unzip proot-distro termux-services -y
   ```

2. **Clone & Setup**:
   ```bash
   git clone <your-repo-url>
   cd fast-media-bot
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure**:
   - Copy `config.env.example` to `config.env`.
   - Fill in your `API_ID`, `API_HASH`, `BOT_TOKEN`, `MONGODB_URI`, and `OWNER_ID`.

4. **Run**:
   ```bash
   python bot.py
   ```

5. **Run as Service (Optional)**:
   Use `pm2` or `termux-services` to keep the bot running in the background.

## 🐳 DOCKER DEPLOYMENT

```bash
docker-compose up -d --build
```

## ⚙️ CONFIGURATION

| Variable | Description |
|----------|-------------|
| `API_ID` | Telegram API ID |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | Main Bot Token |
| `MONGODB_URI` | MongoDB Connection String |
| `OWNER_ID` | Your User ID |
| `HELPER_BOT_TOKENS` | Space-separated bot tokens |
| `SESSION_STRINGS` | Space-separated Pyrogram session strings |

## 🌍 COMMANDS
- `/start`: Admin welcome and panel.
- `/settings`: Admin control panel.
- `/language <lang>`: Set preferred audio language (e.g., `/language Hindi`).
