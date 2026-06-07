import os
import io
import telebot
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode

# Initialize Bot with Token from Environment Variable
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("ERROR: BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(TOKEN)

# ----------------- TELEGRAM BOT LOGIC -----------------

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **ยินดีต้อนรับสู่บอท QR Code Tool!**\n\n"
        "สลับมาเป็นโหมดเครื่องมือใช้งานฟรีเต็มรูปแบบแล้วครับ:\n"
        "📝 **วิธีสร้าง QR Code:** ส่งข้อความ หรือ ลิงก์ (URL) มาได้เลย บอทจะแปลงเป็นคิวอาร์โค้ดให้ทันที\n"
        "📷 **วิธีสแกน QR Code:** ส่งรูปภาพที่มี QR Code มาให้บอท บอทจะอ่านข้อความด้านในให้ครับ"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_text_to_qr(message):
    text = message.text
    
    # Ignore commands
    if text.startswith('/'):
        return

    status_msg = bot.reply_to(message, "⏳ กำลังสร้าง QR Code สักครู่ครับ...")
    
    try:
        # Generate QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to memory buffer
        bio = io.BytesIO()
        bio.name = 'qrcode.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        
        # Send back to user
        bot.delete_message(message.chat.id, status_msg.message_id)
        bot.send_photo(message.chat.id, bio, caption=f"✅ สร้าง QR Code สำเร็จแล้ว!")
    except Exception as e:
        bot.edit_message_text("❌ เกิดข้อผิดพลาดในการสร้าง QR Code กรุณาลองใหม่อีกครั้ง", message.chat.id, status_msg.message_id)

@bot.message_handler(content_types=['photo'])
def handle_qr_scanner(message):
    status_msg = bot.reply_to(message, "⏳ กำลังสแกนรูปภาพเพื่อหา QR Code...")
    
    try:
        # Download the highest resolution photo
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Open image with Pillow
        image = Image.open(io.BytesIO(downloaded_file))
        
        # Decode QR Code
        decoded_objects = decode(image)
        
        if not decoded_objects:
            bot.edit_message_text("❌ ไม่พบ QR Code ในรูปภาพนี้ กรุณาส่งรูปที่ชัดเจนกว่านี้ครับ", message.chat.id, status_msg.message_id)
            return
            
        # Extract data
        qr_data = decoded_objects[0].data.decode('utf-8')
        
        result_text = f"🔍 **ผลการสแกน QR Code:**\n\n`{qr_data}`"
        bot.delete_message(message.chat.id, status_msg.message_id)
        bot.reply_to(message, result_text, parse_mode='Markdown')
        
    except Exception as e:
        bot.edit_message_text("❌ เกิดข้อผิดพลาดในการสแกนรูปภาพ", message.chat.id, status_msg.message_id)

# ----------------- START LONG POLLING -----------------

if __name__ == "__main__":
    print("Bot is starting via Long Polling...")
    # Remove any existing webhooks so polling works cleanly
    bot.remove_webhook()
    # non_stop=True keeps the bot running even if it hits a minor network error
    bot.infinity_polling(non_stop=True)
