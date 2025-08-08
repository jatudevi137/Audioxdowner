import os, tempfile, glob
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from yt_dlp import YoutubeDL

# BotFather Token aus Railway-Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# yt-dlp Einstellungen -> nur Audio (MP3)
YDL_OPTS = {
    "quiet": True,
    "format": "bestaudio/best",
    "noplaylist": True,
    "outtmpl": "%(title).60s.%(ext)s",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Schick mir einfach den Link vom Instagram Reel / TikTok / YouTube Short – ich schick dir nur den Sound als MP3 zurück 🎵"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not any(x in url for x in ["instagram.com", "tiktok.com", "youtu"]):
        await update.message.reply_text("Bitte schick mir einen gültigen Link 📎")
        return

    await update.message.reply_text("🎧 Lade Audio herunter... bitte kurz warten")

    with tempfile.TemporaryDirectory() as tmpdir:
        opts = YDL_OPTS.copy()
        opts["paths"] = {"home": tmpdir, "temp": tmpdir}
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                mp3_files = glob.glob(os.path.join(tmpdir, "*.mp3"))
                if not mp3_files:
                    await update.message.reply_text("⚠️ Konnte keine MP3 erstellen (evtl. ffmpeg-Fehler)")
                    return
                mp3_path = mp3_files[0]
                with open(mp3_path, "rb") as f:
                    await update.message.reply_audio(f, filename=os.path.basename(mp3_path))
        except Exception as e:
            await update.message.reply_text(f"Fehler: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()
YDL_OPTS = {
    "quiet": True,
    "format": "bestaudio/best",
    "noplaylist": True,
    "outtmpl": "%(title).60s.%(ext)s",
    "cookiefile": "cookies.txt",  # <--- NEU
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}
