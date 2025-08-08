import os, tempfile, glob, pathlib, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from yt_dlp import YoutubeDL

# --- Logging einschalten ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
print("🚀 Starte Bot-Prozess…")

# --- ENV Variablen prüfen ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN ist NICHT gesetzt. Geh in Railway → Service → Variables und setz BOT_TOKEN.")

COOKIES_ENV = os.getenv("IG_COOKIES", "")
if COOKIES_ENV:
    print("🍪 IG_COOKIES erkannt (Länge:", len(COOKIES_ENV), ").")
else:
    print("ℹ️ IG_COOKIES nicht gesetzt – öffentliche Reels sollten trotzdem gehen.")

def get_cookiefile():
    if not COOKIES_ENV.strip():
        return None
    tmp = pathlib.Path("/tmp/cookies.txt")
    tmp.write_text(COOKIES_ENV, encoding="utf-8")
    return str(tmp)

YDL_OPTS_BASE = {
    "quiet": True,
    "format": "bestaudio/best",
    "noplaylist": True,
    "outtmpl": "%(title).60s.%(ext)s",
    "retries": 5,
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    },
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
    ],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✔️ Bot ist online. Schick mir einen Reel/TikTok/Shorts-Link – ich sende dir die MP3 🎵")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()
    if not any(x in url for x in ["instagram.com", "tiktok.com", "youtu"]):
        await update.message.reply_text("Bitte schick mir einen gültigen Link 📎")
        return

    await update.message.reply_text("🎧 Ziehe Audio … bitte kurz warten")
    cookiefile = get_cookiefile()

    with tempfile.TemporaryDirectory() as tmpdir:
        opts = YDL_OPTS_BASE.copy()
        opts["paths"] = {"home": tmpdir, "temp": tmpdir}
        if cookiefile:
            opts["cookiefile"] = cookiefile
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                logging.info("Download-Info: %s", info.get("title", "ohne Titel"))
                mp3s = glob.glob(os.path.join(tmpdir, "*.mp3"))
                if not mp3s:
                    await update.message.reply_text("⚠️ Keine MP3 erstellt (prüfe ffmpeg/Cookies/Link).")
                    return
                with open(mp3s[0], "rb") as f:
                    await update.message.reply_audio(f, filename=os.path.basename(mp3s[0]))
        except Exception as e:
            logging.exception("Fehler beim Extrahieren")
            await update.message.reply_text(f"Fehler: {e}")

def main():
    print("🔧 Baue Telegram-Anwendung…")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("✅ Bot gestartet. Warte auf Nachrichten…")
    app.run_polling()

if __name__ == "__main__":
    main()
