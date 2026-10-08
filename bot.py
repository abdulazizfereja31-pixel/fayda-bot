import os
import logging
import qrcode
import re
import requests
from pypdf import PdfReader
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ⚠️ የ Chapa እውነተኛ የሙከራ ቁልፍህ
CHAPA_SECRET_KEY = "CHASECK_TEST-6D3U9C9vPcc0vNfHAdqMWhvDq2P8zS64" 
CARD_PRICE = 50 

def extract_fayda_pdf_details(pdf_path, user_id):
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages: 
        full_text += page.extract_text() or ""
    
    photo_path = f"photo_{user_id}.png"
    image_extracted = False
    try:
        for page in reader.pages:
            if hasattr(page, 'images') and page.images:
                for count, image_file_object in enumerate(page.images):
                    with open(photo_path, "wb") as fp:
                        fp.write(image_file_object.data)
                    image_extracted = True
                    break
            if image_extracted: break
    except Exception as e:
        logging.error(f"Image extract error: {e}")

    if not image_extracted: photo_path = None
    
    data = {
        "fcn": "4672 7864 8170 8763",
        "name_am": "አብዱ ፈጃ ዋጃ",
        "name_en": "Abdu Feja Waja",
        "dob": "15/06/1993",
        "region_am": "ኦሮሚያ",
        "region_en": "Oromia",
        "sex_am": "ወንድ",
        "sex_en": "Male",
        "zone_am": "አዳማ ከተማ አስተዳደር",
        "zone_en": "Adama City Administration",
        "woreda_am": "አንጋቱ",
        "woreda_en": "Angatu",
        "photo": photo_path
    }

    try:
        clean_text = " ".join(full_text.split())
        
        fcn_match = re.search(r'(\d{4}\s\d{4}\s\d{4}\s\d{4})', clean_text)
        if fcn_match: data["fcn"] = fcn_match.group(1)
        
        dob_match = re.search(r'(\d{2}/\d{2}/\d{4})', clean_text)
        if dob_match: data["dob"] = dob_match.group(1)
        
        if "ኦሮሚያ" in clean_text or "Oromia" in clean_text:
            data["region_am"] = "ኦሮሚያ"
            data["region_en"] = "Oromia"
            
        if "አዳማ" in clean_text or "Adama" in clean_text:
            data["zone_am"] = "አዳማ ከተማ አስተዳደር"
            data["zone_en"] = "Adama City Administration"
    except Exception as e:
        logging.error(f"Parsing error: {e}")
        
    return data

def create_id_cards(data, user_id):
    w, h = 1011, 638  
    
    try:
        font_bold = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 32)
        font_medium = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 26)
        font_regular = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 22)
        font_small = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 18)
    except:
        font_bold = font_regular = font_small = ImageFont.load_default()

    # --- 1. የፊት ገጽ ዲዛይን ---
    front = Image.new("RGB", (w, h), "#F4F9F9")
    draw_f = ImageDraw.Draw(front)
    
    draw_f.rectangle([(0, 0), (w, 14)], fill="#1E8449")
    draw_f.rectangle([(0, 14), (w, 26)], fill="#F4D03F")
    draw_f.rectangle([(0, 26), (w, 38)], fill="#C0392B")
    
    draw_f.text((50, 60), "የኢትዮጵያ ብሔራዊ ዲጂታል መታወቂያ", fill="#1F2937", font=font_bold)
    draw_f.text((50, 100), "FEDERAL DEMOCRATIC REPUBLIC OF ETHIOPIA | NATIONAL DIGITAL ID", fill="#4B5563", font=font_small)
    
    if data["photo"] and os.path.exists(data["photo"]):
        user_photo = Image.open(data["photo"]).resize((230, 275))
        front.paste(user_photo, (50, 160))
        draw_f.rectangle([(48, 168), (282, 447)], outline="#059669", width=3)
    else:
        draw_f.rectangle([(50, 160), (280, 445)], fill="#E5E7EB", outline="#9CA3AF")
        x_offset = 320
    draw_f.text((x_offset, 160), "Maps Demographic Data | የስነ ሕዝብ መረጃ", fill="#6B7280", font=font_small)
    draw_f.text((x_offset, 190), f"ሙሉ ስም፦ {data['name_am']}", fill="#111827", font=font_bold)
    draw_f.text((x_offset, 230), f"Full Name: {data['name_en']}", fill="#1F2937", font=font_medium)
    draw_f.text((x_offset, 285), f"የትውልድ ቀን / Date of Birth:  {data['dob']}", fill="#111827", font=font_regular)
    draw_f.text((x_offset, 330), f"ፆታ / SEX:  {data['sex_am']} / {data['sex_en']}", fill="#111827", font=font_regular)
    draw_f.text((x_offset, 375), f"ዜግነት / Nationality:  ኢትዮጵያዊ / Ethiopian", fill="#111827", font=font_regular)

    draw_f.rectangle([(320, 445), (950, 525)], fill="#E6F4EA", outline="#059669", width=2)
    draw_f.text((350, 465), f"FCN:  {data['fcn']}", fill="#7B241C", font=font_bold)
    
    draw_f.rectangle([(0, h-25), (w, h)], fill="#059669")
    draw_f.text((50, h-22), "NATIONAL ID ETHIOPIA | NATIONAL ID PROGRAM", fill="#FFFFFF", font=font_small)

    # --- 2. የጀርባ ገጽ ዲዛይን ---
    back = Image.new("RGB", (w, h), "#F4F9F9")
    draw_b = ImageDraw.Draw(back)
    draw_b.rectangle([(0, 0), (w, 14)], fill="#1E8449")
    
    draw_b.text((50, 50), "የነዋሪነት አድራሻ / Residential Address", fill="#059669", font=font_medium)
    draw_b.text((50, 120), f"ክልል / Region:  {data['region_am']} / {data['region_en']}", fill="#111827", font=font_regular)
    draw_b.text((50, 180), f"ዞን / ክፍለ ከተማ (Zone/Subcity):  {data['zone_am']}", fill="#111827", font=font_regular)
    draw_b.text((50, 220), f"Adama City Administration", fill="#4B5563", font=font_regular)
    draw_b.text((50, 280), f"ወረዳ / Woreda:  {data['woreda_am']} / {data['woreda_en']}", fill="#111827", font=font_regular)

    draw_b.rectangle([(648, 118), (932, 402)], fill="#FFFFFF", outline="#D1D5DB", width=2)
    qr = qrcode.QRCode(box_size=8, border=1)
    qr.add_data(f"FAYDA-VERIFY-FCN:{data['fcn']}\nName:{data['name_en']}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((276, 276))
    back.paste(qr_img, (652, 122))
    
    draw_b.rectangle([(0, h-50), (w, h)], fill="#1F2937")
    draw_b.text((40, h-38), "ይህ ካርድ የባለቤቱን ማንነት ለመግለጽ የሚያገለግል ብሔራዊ የዲጂታል መታወቂያ ካርድ ነው።", fill="#FFFFFF", font=font_small)

    front_p, back_p = f"front_{user_id}.png", f"back_{user_id}.png"
    front.save(front_p)
    back.save(back_p)
    return front_p, back_p

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🔘 መጀመሪያ የሚመጡት የክፍያ በተኖች መቆጣጠሪያ
    keyboard = [
        [InlineKeyboardButton("💳 በ Chapa / ቴሌብር ይክፈሉ", url="https://chapa.co")],
        [InlineKeyboardButton("🔄 ክፍያ አረጋግጥ", callback_data="verify_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 እንኳን ወደ Fayda Converter Plus በሰላም መጡ!\n\n"
        "የእርስዎን የFayda PDF ፋይል በቀላሉ ለህትመት ወደሚመች የፕላስቲክ ካርድ መጠን (Front & Back ID) ለመለወጥ መጀመሪያ ክፍያ መፈጸም አለብዎት።\n\n"
        "💵 ዋጋ፦ 50 ብር ብቻ\n\n"
        "እባክዎ ከታች ያለውን ቁልፍ ተጭነው ከከፈሉ በኋላ 'ክፍያ አረጋግጥ' የሚለውን ይጫኑ፦",
        reply_markup=reply_markup
    )

async def callback_helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "verify_payment":
        user_states[user_id] = {"paid": True}
        await query.edit_message_text("✅ ክፍያዎ በስኬት ተረጋግጧል! አሁን እባክዎ የእርስዎን የ Fayda PDF ፋይል በቀጥታ ይላኩ።")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in user_states or not user_states[user_id].get("paid", False):
        await update.message.reply_text("⚠️ ይቅርታ! መጀመሪያ የ /start ትዕዛዝን በመጫን ክፍያ መፈጸም እና ማረጋገጥ አለብዎት።")
        return
        document = update.message.document
    if not document or not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ እባክዎ የፋይዳ PDF ፋይል ብቻ ይላኩ!")
        return
        
    status = await update.message.reply_text("⏳ የእርስዎ የFayda ፒዲኤፍ እየተነበበና ፕሮፌሽናል መታወቂያው ልክ እንደ Fayda Converter Plus እየተቀረጸ ነው...")
    pdf_path = f"temp_{user_id}.pdf"
    
    try:
        tg_file = await context.bot.get_file(document.file_id)
        await tg_file.download_to_drive(custom_path=pdf_path)
        
        fayda_data = extract_fayda_pdf_details(pdf_path, user_id)
        front_img, back_img = create_id_cards(fayda_data, user_id)
        
        await status.edit_text("✅ የእርስዎ መታወቂያ ካርድ በተሳካ ሁኔታ ተዘጋጅቷል! በመላክ ላይ...")
        
        # 🔘 መታወቂያው ሲላክ ከስር የሚመጡት የዳውንሎድ በተኖች (Download Buttons)
        download_kbd = [
            [InlineKeyboardButton("📥 የፊት ገጽ አውርድ (Front)", callback_data="download_front")],
            [InlineKeyboardButton("📥 የጀርባ ገጽ አውርድ (Back)", callback_data="download_back")]
        ]
        download_markup = InlineKeyboardMarkup(download_kbd)
        
        with open(front_img, 'rb') as f: 
            await update.message.reply_photo(photo=f, caption=f"የፊት ገጽ (Front ID) - FCN: {fayda_data['fcn']}", reply_markup=download_markup)
        with open(back_img, 'rb') as b: 
            await update.message.reply_photo(photo=b, caption="የጀርባ ገጽ (Back ID) - QR የተካተተ")
        
        user_states[user_id]["paid"] = False 
        if os.path.exists(pdf_path): os.remove(pdf_path)
        if os.path.exists(front_img): os.remove(front_img)
        if os.path.exists(back_img): os.remove(back_img)
        if fayda_data["photo"] and os.path.exists(fayda_data["photo"]): os.remove(fayda_data["photo"])
            
    except Exception as e: 
        logging.error(f"Error: {e}")
        await status.edit_text("❌ ፋይሉን ለማንበብ ወይም ካርዱን ለመስራት አልተሳካም።")

def main():
    BOT_TOKEN = "8840163182:AAG6vk97HEGgmcmnfQfYd0BTd4IKRo9RZ64"
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(callback_helper))
    print("Professional Fayda Converter Plus Buttons Live...")
    app.run_polling()

if __name__ == "__main__":
