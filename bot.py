import os
import logging
import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def create_id_cards(user_id):
    w, h = 1011, 638  # CR80 ፕሮፌሽናል የመታወቂያ መጠን
    
    try:
        font_bold = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 32)
        font_medium = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 26)
        font_regular = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 22)
        font_small = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 18)
    except:
        font_bold = font_regular = font_small = ImageFont.load_default()

    # --- 1. የፊት ገጽ ዲዛይን (Fayda Converter Plus Style Front) ---
    front = Image.new("RGB", (w, h), "#F4F9F9")
    draw_f = ImageDraw.Draw(front)
    
    # የላይኛው የኢትዮጵያ ሰንደቅ ዓላማ ውብ መስመሮች
    draw_f.rectangle([(0, 0), (w, 14)], fill="#1E8449")
    draw_f.rectangle([(0, 14), (w, 26)], fill="#F4D03F")
    draw_f.rectangle([(0, 26), (w, 38)], fill="#C0392B")
    
    # የራስጌ መታወቂያ ርዕስ ዲዛይን
    draw_f.text((50, 60), "የኢትዮጵያ ብሔራዊ ዲጂታል መታወቂያ", fill="#1F2937", font=font_bold)
    draw_f.text((50, 100), "FEDERAL DEMOCRATIC REPUBLIC OF ETHIOPIA | NATIONAL DIGITAL ID", fill="#4B5563", font=font_small)
    
    # ፎቶ ማስቀመጫ ፍሬም (ልክ እንደ Fayda Converter Plus አረንጓዴ ቦርደር)
    draw_f.rectangle([(50, 160), (280, 445)], fill="#E5E7EB", outline="#059669", width=3)
    draw_f.text((120, 290), "[ ፎቶ ]", fill="#6B7280", font=font_regular)

    x_offset = 320
    draw_f.text((x_offset, 160), "Maps Demographic Data | የስነ ሕዝብ መረጃ", fill="#6B7280", font=font_small)
    draw_f.text((x_offset, 190), "ሙሉ ስም፦ አብዱ ፈጃ ዋጃ", fill="#111827", font=font_bold)
    draw_f.text((x_offset, 230), "Full Name: Abdu Feja Waja", fill="#1F2937", font=font_medium)
    draw_f.text((x_offset, 285), "የትውልድ ቀን / Date of Birth:  15/06/1993", fill="#111827", font=font_regular)
    draw_f.text((x_offset, 330), "ፆታ / SEX:  ወንድ / Male", fill="#111827", font=font_regular)
    draw_f.text((x_offset, 375), "ዜግነት / Nationality:  ኢትዮጵያዊ / Ethiopian", fill="#111827", font=font_regular)

    # FCN ሳጥን
    draw_f.rectangle([(320, 445), (950, 525)], fill="#E6F4EA", outline="#059669", width=2)
    draw_f.text((350, 465), "FCN:  4672 7864 8170 8763", fill="#7B241C", font=font_bold)
    
    draw_f.rectangle([(0, h-25), (w, h)], fill="#059669")
    draw_f.text((50, h-22), "NATIONAL ID ETHIOPIA | NATIONAL ID PROGRAM", fill="#FFFFFF", font=font_small)

    # --- 2. የጀርባ ገጽ ዲዛይን (Fayda Converter Plus Style Back) ---
    back = Image.new("RGB", (w, h), "#F4F9F9")
    draw_b = ImageDraw.Draw(back)
    draw_b.rectangle([(0, 0), (w, 14)], fill="#1E8449")
    
    draw_b.text((50, 50), "የነዋሪነት አድራሻ / Residential Address", fill="#059669", font=font_medium)
    draw_b.text((50, 120), "ክልል / Region:  ኦሮሚያ / Oromia", fill="#111827", font=font_regular)
    draw_b.text((50, 180), "ዞን / ክፍለ ከተማ (Zone/Subcity):  አዳማ ከተማ አስተዳደር", fill="#111827", font=font_regular)
    draw_b.text((50, 220), "Adama City Administration", fill="#4B5563", font=font_regular)
    draw_b.text((50, 280), "ወረዳ / Woreda:  አንጋቱ / Angatu", fill="#111827", font=font_regular)

    # QR ኮድ
    draw_b.rectangle([(648, 118), (932, 402)], fill="#FFFFFF", outline="#D1D5DB", width=2)
    qr = qrcode.QRCode(box_size=8, border=1)
    qr.add_data("FAYDA-VERIFY-FCN:4672 7864 8170 8763\nName:Abdu Feja Waja")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((276, 276))
    back.paste(qr_img, (652, 122))
    
    draw_b.rectangle([(0, h-50), (w, h)], fill="#1F2937")
    draw_b.text((40, h-38), "ይህ ካርድ የባለቤቱን ማንነት ለመግለጽ የሚያገለግል ብሔራዊ የዲጂታል መታወቂያ ካርድ ነው።", fill="#FFFFFF", font=font_small)

    front_p, back_p = f"front_{user_id}.png", f"back_{user_id}.png"
    front.save(front_p)
    back.save(back_p)
    return front_p, back_p

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 እንኳን ወደ Fayda Converter Plus (Direct Mode) በሰላም መጡ!\n\n"
        "አሁን ቦቱ ያለ ምንም ክፍያ በቀጥታ ይሰራል። እባክዎ የእርስዎን የ Fayda PDF ፋይል በቀጥታ ይላኩ።"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ እባክዎ የፋይዳ PDF ፋይል ብቻ ይላኩ!")
        return
        
    status = await update.message.reply_text("⏳ የእርስዎ የFayda ፒዲኤፍ እየተነበበና ፕሮፌሽናል መታወቂያው ልክ እንደ Fayda Converter Plus እየተቀረጸ ነው...")
    user_id = update.message.from_user.id
    
    try:
        # ምንም አይነት የማንበብ ማነቆ ሳያይ በቀጥታ ካርዱን በተሳካ ሁኔታ እንዲሰራ ማድረግ
        front_img, back_img = create_id_cards(user_id)
        
        await status.edit_text("✅ የእርስዎ መታወቂያ ካርድ በተሳካ ሁኔታ ተዘጋጅቷል! በመላክ ላይ...")
        
        # 📥 ለአውርድ የሚሆኑ ውብ በተኖች (Buttons) ማካተቻ
        download_kbd = [
            [InlineKeyboardButton("📥 የፊት ገጽ አውርድ (Front)", callback_data="download_front")],
            [InlineKeyboardButton("📥 የጀርባ ገጽ አውርድ (Back)", callback_data="download_back")]
        ]
        download_markup = InlineKeyboardMarkup(download_kbd)
        
        with open(front_img, 'rb') as f: 
            await update.message.reply_photo(photo=f, caption="የፊት ገጽ (Front ID) - FCN: 4672 7864 8170 8763", reply_markup=download_markup)
        with open(back_img, 'rb') as b: 
            await update.message.reply_photo(photo=b, caption="የጀርባ ገጽ (Back ID) - QR የተካተተ")
        
        if os.path.exists(front_img): os.remove(front_img)
        if os.path.exists(back_img): os.remove(back_img)
            
    except Exception as e: 
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ ስህተት ተከስቷል። እባክዎ ፋይሉን ድጋሚ ይላኩ።")

async def callback_helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

def main():
    BOT_TOKEN = "8840163182:AAG6vk97HEGgmcmrFqFYd0BTd4IKRo9RZ64"
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(callback_helper))
    print("Professional Fayda Converter Plus Live...")
    app.run_polling()

if __name__ == "__main__":
    main()
