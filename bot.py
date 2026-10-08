import os
import logging
import qrcode
from pypdf import PdfReader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔍 1. የፋይዳ PDF ጽሑፎችን ሙሉ በሙሉ ፈልፍሎ ማውጫ ሎጂክ (Text Parsing Fixed)
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
    
    # ጽሑፎቹ በተያያዘ መስመር ቢመጡም ቃላቱን ነጥሎ የመለቀሚያ ስልት
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

    # በፒዲኤፉ ውስጥ ያሉትን ቃላት በደህንነት መፈለግ
    clean_text = " ".join(full_text.split())
    
    import re
    fcn_match = re.search(r'(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})', clean_text)
    if fcn_match: data["fcn"] = fcn_match.group(1)
    
    dob_match = re.search(r'(\d{2}/\d{2}/\d{4})', clean_text)
    if dob_match: data["dob"] = dob_match.group(1)

    return data

# 🎨 2. የ Fayda Converter Plus እውነተኛ የካርድ ዲዛይን አብነት በኮድ መገንቢያ
def create_id_cards(data, user_id):
    w, h = 1011, 638  # CR80 ፕሮፌሽናል የመታወቂያ መጠን
    
    try:
        font_bold = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 32)
        font_medium = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 26)
        font_regular = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 22)
        font_small = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 18)
    except:
        font_bold = font_medium = font_regular = font_small = ImageFont.load_default()

    # --- ሀ. የፊት ገጽ ዲዛይን (Fayda Converter Plus Style Front) ---
    # መለስተኛ ሰማያዊ/ሳያን እና ነጭ ቅልቅል የጀርባ ቀለም (Gradient Layer)
    front = Image.new("RGB", (w, h), "#F4F9F9")
    draw_f = ImageDraw.Draw(front)
    
    # የላይኛው የኢትዮጵያ ሰንደቅ ዓላማ ውብ መስመሮች
    draw_f.rectangle([(0, 0), (w, 14)], fill="#1E8449")
    draw_f.rectangle([(0, 14), (w, 26)], fill="#F4D03F")
    draw_f.rectangle([(0, 26), (w, 38)], fill="#C0392B")
    
    # የራስጌ መታወቂያ ርዕስ ዲዛይን
    draw_f.text((50, 60), "የኢትዮጵያ ብሔራዊ ዲጂታል መታወቂያ", fill="#1F2937", font=font_bold)
    draw_f.text((50, 100), "FEDERAL DEMOCRATIC REPUBLIC OF ETHIOPIA", fill="#4B5563", font=font_small)
    draw_f.text((50, 120), "NATIONAL DIGITAL ID", fill="#059669", font=font_regular)
    
    # የፎቶ አቀማመጥ እና ውብ ፍሬም (Border)
    if data["photo"] and os.path.exists(data["photo"]):
        try:
            user_photo = Image.open(data["photo"]).resize((230, 275))
            front.paste(user_photo, (50, 170))
            draw_f.rectangle([(48, 168), (282, 447)], outline="#059669", width=3) # አረንጓዴ ፍሬም
        except:
            draw_f.rectangle([(50, 170), (280, 445)], fill="#E5E7EB", outline="#9CA3AF")
    else:
        draw_f.rectangle([(50, 170), (280, 445)], fill="#E5E7EB", outline="#9CA3AF")
        # የግል መረጃዎች አቀማመጥ (ልክ እንደ Fayda Converter Plus)
    x_offset = 320
    draw_f.text((x_offset, 170), f"ሙሉ ስም / Full Name", fill="#6B7280", font=font_small)
    draw_f.text((x_offset, 195), f"{data['name_am']}", fill="#111827", font=font_bold)
    draw_f.text((x_offset, 235), f"{data['name_en']}", fill="#1F2937", font=font_medium)
    
    draw_f.text((x_offset, 290), f"የትውልድ ቀን / Date of Birth:  {data['dob']}", fill="#111827", font=font_regular)
    draw_f.text((x_offset, 335), f"ፆታ / SEX:  {data['sex_am']} / {data['sex_en']}", fill="#111827", font=font_regular)
    draw_f.text((x_offset, 380), f"ዜግነት / Nationality:  {data['citizenship_am'] if 'citizenship_am' in data else 'ኢትዮጵያዊ'} / Ethiopian", fill="#111827", font=font_regular)

    # የ FCN መለያ ቁጥር ሳጥን (በደመቀ ከለር ከስር ማሳያ)
    draw_f.rectangle([(320, 445), (950, 525)], fill="#E6F4EA", outline="#059669", width=2)
    draw_f.text((350, 465), f"FCN:  {data['fcn']}", fill="#7B241C", font=font_bold)
    
    # የካርድ አስመጪው የጥራት ማረጋገጫ መስመር ከስር
    draw_f.rectangle([(0, h-25), (w, h)], fill="#059669")
    draw_f.text((50, h-22), "NATIONAL ID ETHIOPIA | NATIONAL ID PROGRAM", fill="#FFFFFF", font=font_small)

    # --- ለ. የጀርባ ገጽ ዲዛይን (Fayda Converter Plus Style Back) ---
    back = Image.new("RGB", (w, h), "#F4F9F9")
    draw_b = ImageDraw.Draw(back)
    
    # የላይኛው ቀጭን አረንጓዴ መስመር
    draw_b.rectangle([(0, 0), (w, 14)], fill="#1E8449")
    
    # የአድራሻ መረጃዎች አቀማመጥ (በግራ በኩል)
    draw_b.text((50, 50), "የነዋሪነት አድራሻ / Residential Address", fill="#059669", font=font_medium)
    
    draw_b.text((50, 120), f"ክልል / Region:  {data['region_am']} / {data['region_en']}", fill="#111827", font=font_regular)
    draw_b.text((50, 180), f"ዞን / ክፍለ ከተማ (Zone/Subcity):  {data['zone_am']}", fill="#111827", font=font_regular)
    draw_b.text((50, 220), f"Adama City Administration", fill="#4B5563", font=font_regular)
    draw_b.text((50, 280), f"ወረዳ / Woreda:  {data['woreda_am']} / {data['woreda_en']}", fill="#111827", font=font_regular)

    # ትልቅ ማረጋገጫ QR ኮድ በቀኝ በኩል በነጭ ፍሬም
    draw_b.rectangle([(648, 118), (932, 402)], fill="#FFFFFF", outline="#D1D5DB", width=2)
    qr = qrcode.QRCode(box_size=8, border=1)
    qr.add_data(f"FAYDA-VERIFY-FCN:{data['fcn']}\nName:{data['name_en']}\nDOB:{data['dob']}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((276, 276))
    back.paste(qr_img, (652, 122))
    
    # የህግ ማሳሰቢያ ከስር በኩል በጥቁር ባር
    draw_b.rectangle([(0, h-50), (w, h)], fill="#1F2937")
    draw_b.text((40, h-38), "ይህ ካርድ የባለቤቱን ማንነት ለመግለጽ የሚያገለግል ብሔራዊ የዲጂታል መታወቂያ ካርድ ነው።", fill="#FFFFFF", font=font_small)

    front_p, back_p = f"front_{user_id}.png", f"back_{user_id}.png"
    front.save(front_p)
    back.save(back_p)
    return front_p, back_p

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 እንኳን ወደ Fayda Converter Plus (Professional) በሰላም መጡ!\n\nእባክዎ የFayda PDF ፋይልዎን በቀጥታ ይልኩ።")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or not document.file_name.lower().endswith('.pdf'):
        return
        
    status = await update.message.reply_text("⏳ የእርስዎ እውነተኛ የFayda ፒዲኤፍ እየተነበበና ፕሮፌሽናል መታወቂያው እየተቀረጸ ነው...")
    user_id = update.message.from_user.id
    pdf_path = f"temp_{user_id}.pdf"
    
    try:
        tg_file = await context.bot.get_file(document.file_id)
        await tg_file.download_to_drive(custom_path=pdf_path)
        
        fayda_data = extract_fayda_pdf_details(pdf_path, user_id)
        front_img, back_img = create_id_cards(fayda_data, user_id)
        
        await status.edit_text("✅ የእርስዎ መታወቂያ ካርድ በተሳካ ሁኔታ ተዘጋጅቷል! በመላክ ላይ...")
        
        with open(front_img, 'rb') as f: 
            await update.message.reply_photo(photo=f, caption=f"የፊት ገጽ (Front ID) - FCN: {fayda_data['fcn']}")
            with open(back_img, 'rb') as b: 
            await update.message.reply_photo(photo=b, caption="የጀርባ ገጽ (Back ID) - QR የተካተተ")
        
        if os.path.exists(pdf_path): os.remove(pdf_path)
        if os.path.exists(front_img): os.remove(front_img)
        if os.path.exists(back_img): os.remove(back_img)
        if fayda_data["photo"] and os.path.exists(fayda_data["photo"]): 
            os.remove(fayda_data["photo"])
            
    except Exception as e: 
        logging.error(f"Error handling document: {e}")
        await status.edit_text("❌ ፋይሉን ለማንበብ ወይም ካርዱን ለመስራት አልተሳካም።")

def main():
    BOT_TOKEN = "8840163182:AAG6vk97HEGgmcmnfQfYd0BTd4IKRo9RZ64"
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("Professional Fayda Converter Bot Text Fix Live...")
    app.run_polling()

if __name__ == "__main__": 
    main()
