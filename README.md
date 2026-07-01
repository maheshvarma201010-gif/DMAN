# 🚀 FAST MEDIA DOWNLOADER BOT (Termux, Docker & Colab Optimized)

An extremely fast, optimized Telegram bot for processing videos/audio with multi-language track selection. Optimized for 100% stability across all platforms.

---

## ⚙️ CORE FEATURES
- **FFmpeg Powered:** High-speed remuxing with `ultrafast` preset.
- **Audio Selection:** Extracts specific language tracks from multi-audio files.
- **Auto DNS:** Built-in resolver fallback for restricted environments (Termux/Colab).
- **Helper Bots:** Load-balanced downloading using multiple bot tokens.
- **Robust DB:** MongoDB with automatic retry and SRV resolution fixes.

---

## 🌍 ACCESS CONTROL RULES
- **Admin Commands (`/start`, `/settings`, etc.):** Restricted to `OWNER_ID` or added admins.
- **Language Selection (`/language`):** **OPEN TO ALL USERS.** Any user can set their preferred audio track.
- **Media Processing:**
  - Works for **ALL USERS** if the file is sent in the `AUTH_CHAT_ID`.
  - Works for the **OWNER** anywhere (Private DMs or any chat).

---

## 📱 TERMUX SETUP (Step-by-Step)

1. **Install Termux** from F-Droid.
2. **Setup:**
   ```bash
   pkg install git -y
   git clone <repo_url>
   cd fast-media-bot
   bash setup.sh
   ```
3. **Configure:** Create `config.env` and fill in your credentials.
4. **Run:**
   ```bash
   python bot.py
   ```

---

## 🐳 DOCKER DEPLOYMENT

1. **Build:** `docker build -t fast-media-bot .`
2. **Run:**
   ```bash
   docker run --env-file config.env --name fast-media-bot -v $(pwd)/sessions:/app/sessions fast-media-bot
   ```

---

## 📓 GOOGLE COLAB DEPLOYMENT

1. Open a new Notebook.
2. Run these cells:
   ```python
   !git clone <repo_url>
   %cd fast-media-bot
   !pip install -r requirements.txt
   !apt-get install ffmpeg
   ```
3. Create the `config.env` file in the file explorer.
4. Run:
   ```python
   !python bot.py
   ```

---

## 🌍 ENVIRONMENT VARIABLES (`config.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | Yes | Your API ID from my.telegram.org |
| `API_HASH` | Yes | Your API HASH from my.telegram.org |
| `BOT_TOKEN` | Yes | Bot token from @BotFather |
| `MONGODB_URI` | Yes | MongoDB connection string |
| `OWNER_ID` | Yes | Your Telegram User ID |
| `AUTH_CHAT_ID` | No | Group ID where anyone can process files |
| `HELPER_BOT_TOKENS` | No | Space-separated tokens for extra speed |

---

## 🛠️ TROUBLESHOOTING

- **"Another instance is running":** The bot automatically detects if a previous instance crashed and will overwrite the `bot.lock` file.
- **DNS Errors:** The bot automatically falls back to Google (8.8.8.8) if system DNS fails.
- **Media not processing:** Ensure you are the `OWNER` or you are sending the file in the `AUTH_CHAT_ID`.
