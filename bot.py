import os
import vobject
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

TOKEN = "7698802031:AAFr2i6OKylaS6Vrgso1AmbqhiYncLVkXxQ"  # Ganti dengan token bot Anda

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 ZAFIAN BOT CV\n\n"
        "Kirim file TXT berisi nomor HP (1 nomor per baris)\n"
        "Contoh:\n08123456789\n0876543210\n\n"
        "Setelah upload, reply dengan format:\n"
        "<nama kontak>,<nama file vcf>,<jumlah kontak per file>\n"
        "Contoh: ZAF,HK-1,50"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Download file
        file = await update.message.document.get_file()
        input_path = f"input_{update.message.from_user.id}.txt"
        await file.download_to_drive(input_path)
        
        # Simpan info file
        context.user_data['file_path'] = input_path
        await update.message.reply_text(
            f"📄 File diterima. Total kontak: {sum(1 for _ in open(input_path, 'r', encoding='utf-8'))}\n\n"
            "Reply dengan format:\n"
            "<nama kontak>,<nama file vcf>,<jumlah kontak per file>\n"
            "Contoh: ZAF,HK-1,50"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if 'file_path' not in context.user_data:
            return
            
        input_path = context.user_data['file_path']
        reply_text = update.message.text.strip()
        
        # Parsing parameter
        params = reply_text.split(',')
        if len(params) != 3:
            raise ValueError("Format harus: kontak,nama_file,jumlah_kontak_per_file")
            
        name_prefix = params[0]
        file_prefix = params[1]
        contacts_per_file = int(params[2])
        
        # Baca nomor HP
        with open(input_path, 'r', encoding='utf-8') as f:
            numbers = [line.strip() for line in f if line.strip()]
        
        total_numbers = len(numbers)
        total_files = (total_numbers + contacts_per_file - 1) // contacts_per_file
        
        # Proses pembuatan VCF
        global_counter = 1  # Penghitung global untuk nomor urut
        
        for file_num in range(1, total_files + 1):
            output_file = f"{file_prefix}{file_num}.vcf"
            start_idx = (file_num - 1) * contacts_per_file
            end_idx = start_idx + contacts_per_file
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for num in numbers[start_idx:end_idx]:
                    vcard = vobject.vCard()
                    vcard.add('fn').value = f"{name_prefix} {global_counter}"  # Nomor urut global
                    vcard.add('tel').value = num
                    f.write(vcard.serialize())
                    global_counter += 1  # Increment counter
            
            # Kirim file ke user
            with open(output_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=output_file,
                    caption=f"File {file_num}: Kontak {start_idx + 1}-{min(end_idx, total_numbers)}"
                )
            os.remove(output_file)
        
        await update.message.reply_text(
            f"✅ Berhasil membuat {total_files} file VCF\n"
            f"Total kontak diproses: {total_numbers}\n"
            f"Nomor urut: 1-{total_numbers}"
        )
        
        # Bersihkan file
        os.remove(input_path)
        del context.user_data['file_path']
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.TEXT, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply))
    
    application.run_polling()

if __name__ == "__main__":
    main()