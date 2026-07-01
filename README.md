# 🚀 FAST MEDIA DOWNLOADER BOT (Termux & Docker Optimized)

An extremely fast, optimized Telegram bot for processing videos/audio with multi-language track selection. Optimized for 100% stability in Termux and Docker.

---

## ⚙️ CORE FEATURES
- **FFmpeg Powered:** High-speed remuxing with `ultrafast` preset.
- **Audio Selection:** Extracts specific language tracks from multi-audio files.
- **Termux Fixes:** Built-in DNS resolver fallback and instance locking to prevent SQLite crashes.
- **Helper Bots:** Load-balanced downloading using multiple bot tokens.
- **Robust DB:** MongoDB with automatic retry and SRV resolution fixes.

---

## 📱 TERMUX SETUP (Step-by-Step)

> **IMPORTANT:** Ensure you set `OWNER_ID` in your `config.env` so the bot recognizes you as the admin.


1. **Install Termux** from F-Droid (not Play Store).
2. **Update Packages:**
   ```bash
   pkg update && pkg upgrade
   ```
3. **Install Dependencies:**
   ```bash
   pkg install python ffmpeg nodejs-lts git
   ```
4. **Clone & Setup:**
   ```bash
   git clone <repo_url>
   cd fast-media-bot
   pip install -r requirements.txt
   ```
5. **Configure:**
   Rename `config.env` and fill in your credentials:
   ```bash
   nano config.env
   ```
6. **Run:**
   ```bash
   python bot.py
   ```

---

## 🐳 DOCKER DEPLOYMENT

1. **Build Image:**
   ```bash
   docker build -t fast-media-bot .
   ```
2. **Run Container:**
   ```bash
   docker run --env-file config.env --name fast-media-bot -v $(pwd)/sessions:/app/sessions fast-media-bot
   ```

---

## 🌍 ENVIRONMENT VARIABLES (`config.env`)

| Variable | Description |
|----------|-------------|
| `API_ID` | Your API ID from my.telegram.org |
| `API_HASH` | Your API HASH from my.telegram.org |
| `BOT_TOKEN` | Bot token from @BotFather |
| `MONGODB_URI` | MongoDB connection string (Atlas or Local) |
| `OWNER_ID` | Your Telegram User ID |
| `AUTH_CHAT_ID` | Admin chat ID (defaults to Owner ID) |
| `HELPER_BOT_TOKENS` | Space-separated tokens of helper bots |

---

## 🧾 COMMANDS
- `/start` → Admin only panel.
- `/language` → Set preferred audio language.
- `/settings` → Admin control panel.
- `/status` → Bot health & system info.

---

## 🛠️ TROUBLESHOOTING

- **"Another instance is running":** Delete `bot.lock` if the bot crashed unexpectedly.
- **DNS Errors:** The bot automatically falls back to Google (8.8.8.8) if Termux fails to read system DNS.
- **DB Connection Timeout:** Check if your IP is whitelisted in MongoDB Atlas.
