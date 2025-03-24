import os
import vobject
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konfigurasi Railway
TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_URL = os.getenv("RAILWAY_STATIC_URL", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Hai {user.mention_markdown()}!\n\n"
        "📱 TXT to VCF Converter Bot\n"
        "Kirim file TXT berisi nomor HP (satu nomor per baris)\n\n"
        "Contoh format file:\n"
        "08123456789\n"
        "0876543210"
    )

async def handle_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk file TXT"""
    try:
        # Download file
        file = await update.message.document.get_file()
        input_path = f"input_{update.message.from_user.id}.txt"
        await file.download_to_drive(input_path)
        
        # Baca nomor HP
        with open(input_path, "r", encoding="utf-8") as f:
            numbers = [line.strip() for line in f if line.strip()]
        
        if not numbers:
            await update.message.reply_text("❌ File kosong atau format salah!")
            return

        # Buat VCF
        output_path = f"output_{update.message.from_user.id}.vcf"
        with open(output_path, "w", encoding="utf-8") as f:
            for idx, number in enumerate(numbers, start=1):
                vcard = vobject.vCard()
                vcard.add('fn').value = f"Kontak-{idx}"
                vcard.add('tel').value = number
                f.write(vcard.serialize() + "\n")
        
        # Kirim file ke user
        with open(output_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="kontak.vcf",
                caption=f"✅ {len(numbers)} nomor berhasil dikonversi!"
            )
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Gagal memproses file. Coba lagi atau hubungi admin.")
    
    finally:
        # Bersihkan file temporary
        for file_path in [input_path, output_path]:
            if os.path.exists(file_path):
                os.remove(file_path)

def main():
    """Start the bot."""
    # Inisialisasi bot
    application = Application.builder().token(TOKEN).build()
    
    # Tambahkan handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.TXT, handle_txt))
    
    # Konfigurasi deploy
    if WEBHOOK_URL:  # Untuk production di Railway
        logger.info("Running in WEBHOOK mode")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"https://{WEBHOOK_URL}/{TOKEN}"
        )
    else:  # Untuk development lokal
        logger.info("Running in POLLING mode")
        application.run_polling()

if __name__ == "__main__":
    logger.info("Starting bot...")
    main()