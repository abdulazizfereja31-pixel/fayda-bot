import os
import logging
import qrcode
from pypdf import PdfReader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        for i, line in enumerate(lines):
            if "FCN:" in line and i + 1 < len(lines): data["fcn"] = lines[i+1]
            if "First, Middle, Surname" in line and i + 2 < len(lines):
                data["name_am"] = lines[i+1]
                data["name_en"] = lines[i+2]
            if "Date of Birth" in line and i + 1 < len(lines): data["dob"] = lines[i+1]
            if "Region" in line and i + 2 < len(lines):
                data["region_am"] = lines[i+1]
                data["region_en"] = lines[i+2]
            if "SEX" in line and i + 2 < len(lines):
                data["sex_am"] = lines[i+1]
                data["sex_en"] = lines[i+2]
            if "Subcity / zone" in line and i + 2 < len(lines):
                data["zone_am"] = lines[i+1]
                data["zone_en"] = lines[i+2]
            if "Woreda" in line and i + 2 < len(lines):
                data["woreda_am"] = lines[i+1]
                data["woreda_en"] = lines[i+2]
    except Exception as e: 
        logging.error(f"Parsing error: {e}")
    return data

def create_id_cards(data, user_id):
    w, h = 1011, 638
    
    try:
        font_bold = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 32)
        font_regular = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 24)
        font_small = ImageFont.truetype("NotoSansEthiopic-Regular.ttf", 20)
    except:
        font_bold = font_regular = font_small = ImageFont.load_default()

    front = Image.new("RGB", (w, h), "#FFFFFF")
    draw_f = ImageDraw.Draw(front)
    
    draw_f.rectangle([(0, 0), (w, 20)], fill="#1E8449")
    draw_f.rectangle([(0, 20), (w, 35)], fill="#F4D03F")
    draw_f.rectangle([(0, 35), (w, 50)], fill="#C0392B")
    
    draw_f.text((50, 70), "የኢትዮጵያ ዲጂታል መታወቂያ | Ethiopian Digital ID Card", fill="#1F2937", font=font_bold)
    
    if data["photo"] and os.path.exists(data["photo"]):
        try:
            user_photo = Image.open(data["photo"]).resize((240, 290))
            front.paste(user_photo, (50, 160))
        except:
            draw_f.rectangle([(50, 160), (290, 450)], fill="#E5E7EB", outline="#9CA3AF")
    else:
        draw_f.rectangle([(50, 160), (290, 450)], fill="#E5E7EB", outline="#9CA3AF")
        draw_f.text((330, 160), "ሙሉ ስም / Full Name:", fill="#4B5563", font=font_small)
    draw_f.text((330, 185), f"{data['name_am']}", fill="#111827", font=font_bold)
    draw_f.text((330, 220), f"{data['name_en']}", fill="#111827", font=font_bold)
    draw_f.text((330, 270), f"የትውልድ ቀን / Date of Birth:  {data['dob']}", fill="#111827", font=font_regular)
    draw_f.text((330, 315), f"ፆታ / SEX:  {data['sex_am']} / {data['sex_en']}", fill="#111827", font=font_regular)
    draw_f.text((330, 360), f"ዜግነት / Nationality:  ኢትዮጵያዊ / Ethiopian", fill="#111827", font=font_regular)

    draw_f.rectangle([(330, 430), (950, 510)], fill="#F3F4F6", outline="#D1D5DB")
    draw_f.text((360, 445), f"FCN: {data['fcn']}", fill="#7B241C", font=font_bold)

    back = Image.new("RGB", (w, h), "#FFFFFF")
    draw_b = ImageDraw.Draw(back)
    draw_b.rectangle([(0, 0), (w, 15)], fill="#196F3D")
    
    draw_b.text((50, 60), "የነዋሪነት አድራሻ / Residential Address", fill="#4B5563", font=font_bold)
    draw_b.text((50, 130), f"ክልል / Region:  {data['region_am']} / {data['region_en']}", fill="#111827", font=font_regular)
    draw_b.text((50, 190), f"ዞን / ክፍለ ከተማ:  {data['zone_am']}", fill="#111827", font=font_regular)
    draw_b.text((50, 230), f"Zone / Subcity:  {data['zone_en']}", fill="#111827", font=font_regular)
    draw_b.text((50, 290), f"ወረዳ / Woreda:  {data['woreda_am']} / {data['woreda_en']}", fill="#111827", font=font_regular)

    qr = qrcode.QRCode(box_size=8, border=1)
    qr.add_data(f"FAYDA-VERIFY-FCN:{data['fcn']}\nName:{data['name_en']}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((280, 280))
    back.paste(qr_img, (680, 120))
    
    draw_b.text((50, 540), "ይህ ካርድ የባለቤቱን ማንነት ለመግለጽ የሚያገለግል ብሔራዊ የፊርማ ዲጂታል መታወቂያ ነው።", fill="#6B7280", font=font_small)

    front_p, back_p = f"front_{user_id}.png", f"back_{user_id}.png"
    front.save(front_p)
    back.save(back_p)
    return front_p, back_p

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 እንኳን ወደ ፕሮፌሽናል Fayda Converter ቦት በሰላም መጡ!\n\n"
        "እባክዎ የFayda PDF ፋይልዎን በቀጥታ ይላኩ።"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or not document.file_name.lower().endswith('.pdf'):
        return
        
    status = await update.message.reply_text("⏳ የእርስዎ እውነተኛ የFayda ፒዲኤፍ እየተነበበና መታወቂያው እየተቀረጸ ነው...")
    user_id = update.message.from_user.id
    pdf_path = f"temp_{user_id}.pdf"
    
    try:
        # አዲሱ የቴሌግራም v20+ ፋይል ማውረጃ ስልት
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
        await status.edit_text("❌ ፋይሉን ለማንበብ ወይም ካርዱን ለመስራት አልተሳካም። እባክዎ ትክክለኛ የፋይዳ PDF መሆኑን ያረጋግጡ።")

def main():
    BOT_TOKEN = "8840163182:AAG6vk97HEGgmcmrFqFYd0BTd4IKRo9RZ64"
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("Professional Fayda Converter Bot Fixed Version Live...")
    app.run_polling()

if __name__ == "__main__":
    main()
