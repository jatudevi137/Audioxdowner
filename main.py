import os, tempfile, glob, pathlib
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from yt_dlp import YoutubeDL

# BotFather Token aus Railway-Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Cookies aus ENV in temporäre Datei schreiben (falls vorhanden)
COOKIES_ENV = os.getenv("IG_COOKIES", "")

def get_cookiefile():
    """Schreibt IG_COOKIES aus den Railway Variables in eine temporäre Datei."""
    if not COOKIES_ENV.strip():
        return None
    tmp = pathlib.Path("/tmp/cookies.txt")
    tmp.write_text(COOKIES_ENV, encoding="utf-8")
    return str(tmp)

# yt-dlp Einstellungen -> nur Audio (MP3)
YDL_OPTS_BASE = {
    "quiet": True,
    "format": "bestaudio/best",
    "noplaylist": True,
    "outtmpl": "%(title).60s.%(ext)s",
    "retries": 5,
    "http_headers": {  # hilft gegen IG-Rate-Limits
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    },
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
    ],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Schick mir einfach den Link vom Instagram Reel / TikTok / YouTube Short – ich schick dir nur den Sound als MP3 🎵"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()
    if not any(x in url for x in ["instagram.com", "tiktok.com", "youtu"]):
        await update.message.reply_text("Bitte schick mir einen gültigen Link 📎")
        return

    await update.message.reply_text("🎧 Lade Audio herunter... bitte kurz warten")
    cookiefile = get_cookiefile()

    with tempfile.TemporaryDirectory() as tmpdir:
        opts = YDL_OPTS_BASE.copy()
        opts["paths"] = {"home": tmpdir, "temp": tmpdir}
        if cookiefile:
            opts["cookiefile"] = cookiefile
        try:
            with YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
                mp3_files = glob.glob(os.path.join(tmpdir, "*.mp3"))
                if not mp3_files:
                    await update.message.reply_text("⚠️ Konnte keine MP3 erstellen (prüfe ffmpeg / Link / Cookies).")
                    return
                with open(mp3_files[0], "rb") as f:
                    await update.message.reply_audio(f, filename=os.path.basename(mp3_files[0]))
        except Exception as e:
            await update.message.reply_text(f"Fehler: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()
