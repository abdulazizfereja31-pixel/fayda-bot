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
            for count, image_file_object in enumerate(page.images):
                with open(photo_path, "wb") as fp:
                    fp.write(image_file_object.data)
                image_extracted = True
                break
            if image_extracted: break
    except Exception as e:
        logging.error(f"Image extract error: {e}")

    if not image_extracted: photo_path = None
    
    return {
        "name_am": "ዮሐንስ አበበ ታሰሰ", 
        "name_en": "YOHANNES ABEBE TASSEW", 
        "fin": "FIN-9876-5432-1012", 
        "dob": "25/04/1998", 
        "issue_date": "15/01/2026", 
        "photo": photo_path
    }

def create_id_cards(data, user_id):
    w, h = 1011, 638
    front = Image.new("RGB", (w, h), "#F4F6F7")
    draw = ImageDraw.Draw(front)
    draw.rectangle([(0, 0), (w, 85)], fill="#196F3D")
    
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except:
        font_title = font_text = ImageFont.load_default()
        
    draw.text((40, 25), "National ID Card | Fayda", fill="#FFFFFF", font=font_title)
    
    if data["photo"] and os.path.exists(data["photo"]):
        user_photo = Image.open(data["photo"]).resize((220, 260))
        front.paste(user_photo, (50, 150))
    else: 
        draw.rectangle([(50, 150), (270, 410)], fill="#BDC3C7")
        
    draw.text((300, 150), f"Full Name: {data['name_en']}", fill="#2C3E50", font=font_text)
    draw.text((300, 210), f"DOB: {data['dob']}", fill="#2C3E50", font=font_text)
    draw.rectangle([(300, 340), (950, 410)], fill="#EAEDED")
    draw.text((320, 355), f"FIN: {data['fin']}", fill="#7B241C", font=font_title)
    
    back = Image.new("RGB", (w, h), "#F4F6F7")
    draw_b = ImageDraw.Draw(back)
    draw_b.rectangle([(0, 0), (w, 35)], fill="#196F3D")
    draw_b.text((50, 80), f"Issue Date: {data['issue_date']}", fill="#2C3E50", font=font_text)
    
    qr = qrcode.QRCode(box_size=6, border=1)
    qr.add_data(f"FAYDA-VERIFY:{data['fin']}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    back.paste(qr_img, (680, 120))
    
    front_p, back_p = f"front_{user_id}.png", f"back_{user_id}.png"
    front.save(front_p)
    back.save(back_p)
    return front_p, back_p

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 እንኳን ወደ Fayda Converter (የሙከራ ቦት) በሰላም መጡ!\n\n"
        "አሁን ቦቱ ያለ ምንም ክፍያ በቀጥታ ይሰራል። እባክዎ የ Fayda PDF ፋይልዎን ይላኩ።"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ እባክዎ PDF ፋይል ብቻ ይላኩ!")
        return
        
    status = await update.message.reply_text("⏳ የFayda ፒዲኤፍ እየተነበበ ነው... እባክዎ ይጠብቁ...")
    user_id = update.message.from_user.id
    
    try:
        pdf_file = await context.bot.get_file(document.file_id)
        pdf_path = f"temp_{user_id}.pdf"
        await pdf_file.download_to_drive(pdf_path)
        fayda_data = extract_fayda_pdf_details(pdf_path, user_id)
        front_img, back_img = create_id_cards(fayda_data, user_id)
        
        await status.edit_text("✅ ካርዱ ተዘጋጅቷል! በመላክ ላይ...")
        
        with open(front_img, 'rb') as f: await update.message.reply_photo(photo=f, caption="የፊት (Front)")
        with open(back_img, 'rb') as b: await update.message.reply_photo(photo=b, caption="የጀርባ (Back)")
        
        os.remove(pdf_path)
        os.remove(front_img)
        os.remove(back_img)
        if fayda_data["photo"] and os.path.exists(fayda_data["photo"]): 
            os.remove(fayda_data["photo"])
            
    except Exception as e: 
        logging.error(f"Error: {e}")
        await status.edit_text("❌ ፋይሉን መስራት አልተሳካም።")

def main():
    BOT_TOKEN = "8840163182:AAG6vk97HEGgmcmrFqFYd0BTd4IKRo9RZ64"
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("Fayda Converter Plus Bot (Direct Mode) እየሰራ ነው...")
    app.run_polling()

if __name__ == "__main__":
    main()
