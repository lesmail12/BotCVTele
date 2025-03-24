import os
import vobject
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# States untuk ConversationHandler
INPUT_ADMIN_PREFIX, INPUT_NAVY_PREFIX, INPUT_ADMIN_COUNT, INPUT_FILE = range(4)

TOKEN = "8096273049:AAGx69NGCH6i6A7MQ5znHIZnEWXp5VFQDak"  # Ganti dengan token bot Anda

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 **CUSTOM LABEL VCF BOT**\n\n"
        "Masukkan nama untuk kontak ADMIN (contoh: Manager):\n"
        "Ketik /cancel untuk membatalkan"
    )
    return INPUT_ADMIN_PREFIX

async def input_admin_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['admin_prefix'] = update.message.text
    await update.message.reply_text(
        f"✅ Kontak ADMIN: {update.message.text}\n\n"
        "Masukkan nama untuk kontak NAVY (contoh: Navy) atau ketik '-' jika hanya butuh Admin:"
    )
    return INPUT_NAVY_PREFIX

async def input_navy_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    navy_prefix = update.message.text
    if navy_prefix != '-':
        context.user_data['navy_prefix'] = navy_prefix
    await update.message.reply_text(
        f"✅ Kontak NAVY: {navy_prefix if navy_prefix != '-' else 'Tidak ada'}\n\n"
        "Masukkan jumlah kontak ADMIN yang diinginkan (contoh: 3):"
    )
    return INPUT_ADMIN_COUNT

async def input_admin_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        admin_count = int(update.message.text)
        if admin_count < 0:
            raise ValueError
        
        context.user_data['admin_count'] = admin_count
        await update.message.reply_text(
            f"🔢 Jumlah Admin: {admin_count}\n\n"
            "Sekarang kirim file TXT berisi nomor HP (satu nomor per baris)"
        )
        return INPUT_FILE
    
    except ValueError:
        await update.message.reply_text("❌ Harap masukkan angka yang valid!")
        return INPUT_ADMIN_COUNT

async def handle_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Download file
        file = await update.message.document.get_file()
        input_path = f"input_{update.message.from_user.id}.txt"
        await file.download_to_drive(input_path)
        
        # Baca nomor HP
        with open(input_path, "r", encoding="utf-8") as f:
            numbers = [line.strip() for line in f.readlines() if line.strip()]
        
        if not numbers:
            await update.message.reply_text("❌ File tidak berisi nomor yang valid!")
            return ConversationHandler.END
        
        # Ambil parameter dari user
        admin_prefix = context.user_data.get('admin_prefix', 'Admin')
        navy_prefix = context.user_data.get('navy_prefix', None)
        admin_count = context.user_data.get('admin_count', 0)
        
        # Tentukan nama file output
        if navy_prefix and admin_count > 0:
            output_filename = f"{admin_prefix}+{navy_prefix}.vcf"
        elif admin_count > 0:
            output_filename = f"{admin_prefix}.vcf"
        else:
            output_filename = f"{navy_prefix}.vcf"
        
        output_path = f"output_{update.message.from_user.id}.vcf"
        
        # Buat VCF dengan format khusus
        with open(output_path, "w", encoding="utf-8") as f:
            admin_num = 0
            navy_num = 0
            
            for idx, number in enumerate(numbers, start=1):
                vcard = vobject.vCard()
                
                if navy_prefix is None or idx <= admin_count:
                    admin_num += 1
                    contact_name = f"{admin_prefix}-{admin_num}"
                else:
                    navy_num += 1
                    contact_name = f"{navy_prefix}-{navy_num}"
                
                vcard.add("fn").value = contact_name
                vcard.add("tel").value = number
                f.write(vcard.serialize() + "\n")
        
        # Kirim ke user
        with open(output_path, "rb") as f:
            caption = f"✅ {len(numbers)} kontak berhasil dibuat:\n"
            if admin_num > 0:
                caption += f"{admin_num} {admin_prefix}\n"
            if navy_num > 0:
                caption += f"{navy_num} {navy_prefix}"
                
            await update.message.reply_document(
                document=f,
                filename=output_filename,
                caption=caption.strip()
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        # Hapus file sementara
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # Bersihkan data user
        for key in ['admin_prefix', 'navy_prefix', 'admin_count']:
            if key in context.user_data:
                del context.user_data[key]
        
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operasi dibatalkan")
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INPUT_ADMIN_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_admin_prefix)],
            INPUT_NAVY_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_navy_prefix)],
            INPUT_ADMIN_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_admin_count)],
            INPUT_FILE: [MessageHandler(filters.Document.TEXT, handle_txt)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()