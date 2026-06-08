import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from supabase import create_client, Client

# --- المتغيرات البيئية وبيانات الربط المحدثة طبقاً لملف الـ env الخاص بك ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
YOUR_TELEGRAM_USERNAME = "Yousef55641" 

SUPABASE_URL = "https://syrpxdwypyisvlmwmmbu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc2MiOiJzdXBhYmFzZSIsInJlZiI6InN5cnB4ZHd5cHlpc3ZsbXdtbWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MjE2MDEsImV4cCI6MjA5NjQ5NzYwMX0.kG2PzNGb3ta9vu58gZrkCYZJ0YTk3VhsNTa-6fiUZ3M"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- المواد بالأسماء العربية والرموز الأيقونية ---
SUBJECTS = {
    "الرياضيات 📐": "math",
    "الفيزياء 🧲": "phys",
    "الكيمياء ⚗️": "chem",
    "علم الأحياء 🔬": "science",
    "التربية الإسلامية 🕋": "islamic",
    "اللغة العربية 📚": "arabic",
    "اللغة الإنجليزية 🇬🇧": "english",
    "اللغة الفرنسية 🇨🇵": "french",
}

CATEGORIES = {
    "📖 الكتاب المدرسي": "book",
    "📝 الملخصات الذهنية": "notes",
    "📒 النوط الشاملة": "notebook",
    "💡 ملاحظات تذكيرية": "remarks",
    "📅 أسئلة الدورات (حسب السنة)": "exams_year",
    "📝 أسئلة الدورات (كاملة الشرح)": "exams_all",
    "🔍 أسئلة الدورات (حسب الأبحاث)": "exams_topic",
    "🔊 الأحاديث الشريفة": "hadith_audio",
    "🔊 الآيات القرآنية": "quran_audio"
}

def register_student_to_supabase(user):
    try:
        supabase.table("students").upsert({
            "telegram_id": user.id, 
            "username": user.username, 
            "first_name": user.first_name
        }, on_conflict="telegram_id").execute()
    except Exception as e:
        print(f"Error registering student: {e}")

# --- لوحات المفاتيح السفلية المنسقة ---
def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("البكلوريا العلمي 🎓"), KeyboardButton("📢 طلب إعلان للمكتبة")],
        [KeyboardButton("💬 تواصل مع الإدارة")]
    ], resize_keyboard=True, input_field_placeholder="اختر من القائمة الرئيسية...")

def get_subjects_keyboard():
    keys = list(SUBJECTS.keys())
    return ReplyKeyboardMarkup([
        [keys[0], keys[1]],
        [keys[2], keys[3]],
        [keys[4], keys[5]],
        [keys[6], keys[7]],
        ["🔙 العودة للقائمة الرئيسية"]
    ], resize_keyboard=True, input_field_placeholder="اختر المادة لتصفح رصيد ملفاتها...")

def get_categories_keyboard(subject_name):
    keyboard = [
        ["📖 الكتاب المدرسي", "📝 الملخصات الذهنية"],
        ["📒 النوط الشاملة", "💡 ملاحظات تذكيرية"],
        ["📂 أسئلة السنوات السابقة"]
    ]
    if "التربية الإسلامية" in subject_name or "🕋" in subject_name:
        keyboard.insert(2, ["🔊 الأحاديث الشريفة", "🔊 الآيات القرآنية"])
    keyboard.append(["🔙 تغيير المادة المحددة"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="اختر القسم المطلوب...")

def get_exams_keyboard():
    return ReplyKeyboardMarkup([
        ["📅 حسب السنة", "📝 كاملة الشرح"],
        ["🔍 حسب الأبحاث"],
        ["🔙 العودة لأقسام المادة"]
    ], resize_keyboard=True, input_field_placeholder="اختر طريقة فرز الأسئلة...")

# --- ميزة التقاط معرفات الملفات تلقائياً ---
async def catch_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        f_id = update.message.document.file_id
        await update.message.reply_text(
            f"📄 **تم التقاط معرف المستند بنجاح!**\n\n`{f_id}`", 
            parse_mode="Markdown"
        )
    elif update.message.audio:
        f_id = update.message.audio.file_id
        await update.message.reply_text(
            f"🔊 **تم التقاط معرف الملف الصوتي بنجاح!**\n\n`{f_id}`", 
            parse_mode="Markdown"
        )

# --- منطق معالجة الرسائل المستقر ذكياً ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_student_to_supabase(update.effective_user)
    context.user_data.clear() 
    
    await update.effective_message.reply_text(
        "👋 **أهلاً بك في بوت المكتبة التعليمية المطور!**\n\n"
        "✨ اضغط على زر البكلوريا العلمي في القائمة بالأسفل لبدء تصفح المحتوى والملفات المحدثة:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def handle_bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    # 🌟 فحص مرن وذكي للعودة أو القائمة الرئيسية لتفادي أخطاء الرموز التعبيرية 🌟
    if "العودة للقائمة الرئيسية" in text or text == "🏠 الرئيسية":
        user_data.clear()
        await update.message.reply_text("🔙 تم العودة للقائمة الرئيسية للخدمات:", reply_markup=get_main_keyboard())
        return

    elif "البكلوريا العلمي" in text or "تصفح المواد" in text or "تغيير المادة" in text:
        await update.message.reply_text("✨ **يرجى اختيار المادة المطلوبة من القائمة الأيقونية المحدثة:**", reply_markup=get_subjects_keyboard(), parse_mode="Markdown")
        return

    elif "طلب إعلان" in text or "تواصل مع الإدارة" in text:
        await update.message.reply_text(f"💬 يمكنك التواصل مباشرة مع إدارة المكتبة والموقع عبر الحساب الرسمي التالي:\n\n🔗 @{YOUR_TELEGRAM_USERNAME}")
        return

    # التحقق من اختيار المادة (بواسطة النص أو الكلمة المفتاحية)
    matched_subject = None
    for k in SUBJECTS.keys():
        if text in k or k in text:
            matched_subject = k
            break

    if matched_subject:
        user_data["current_subject_name"] = matched_subject
        user_data["current_subject_code"] = SUBJECTS[matched_subject]
        await update.message.reply_text(f"✨ لقد فتحت الآن رفوف مادة:\n🎯 *{matched_subject}*\n\nيرجى تحديد التصنيف المراد عرضه من الأزرار بالأسفل:", reply_markup=get_categories_keyboard(matched_subject), parse_mode="Markdown")
        return

    # دخول أرشيف أسئلة السنوات
    if "أسئلة السنوات السابقة" in text or "📂 أسئلة السنوات" in text:
        if "current_subject_code" not in user_data:
            await update.message.reply_text("⚠️ يرجى اختيار المادة أولاً.", reply_markup=get_subjects_keyboard())
            return
        await update.message.reply_text("📅 اختر طريقة عرض الفرز لأسئلة السنوات السابقة:", reply_markup=get_exams_keyboard())
        return

    # العودة لأقسام المادة
    if "العودة لأقسام المادة" in text:
        if "current_subject_name" not in user_data:
            await update.message.reply_text("⚠️ انتهت الجلسة، يرجى إعادة اختيار المادة:", reply_markup=get_subjects_keyboard())
            return
        subject_name = user_data["current_subject_name"]
        await update.message.reply_text(f"📂 تم العودة لقائمة أقسام مادة:\n🎯 *{subject_name}*", reply_markup=get_categories_keyboard(subject_name), parse_mode="Markdown")
        return

    # جلب ومعالجة المحتويات من قاعدة البيانات (فحص مرن للأزرار)
    matched_category_code = None
    cat_map = {
        "حسب السنة": "exams_year",
        "كاملة الشرح": "exams_all",
        "حسب الأبحاث": "exams_topic"
    }
    
    for k, v in cat_map.items():
        if k in text:
            matched_category_code = v
            break
            
    if not matched_category_code:
        for k, v in CATEGORIES.items():
            if k in text or text in k:
                matched_category_code = v
                break

    if matched_category_code:
        if "current_subject_code" not in user_data:
            await update.message.reply_text("⚠️ انتهت الجلسة، يرجى إعادة اختيار المادة:", reply_markup=get_subjects_keyboard())
            return
        
        subject_code = user_data["current_subject_code"]
        await update.message.reply_text("⏳ جاري سحب المستندات والملفات المحدثة من سيرفر الموقع...")
        
        try:
            response = supabase.table("materials").select("*").eq("subject", subject_code).eq("category", matched_category_code).execute()
            files_list = response.data if response.data else []
        except Exception as e:
            await update.message.reply_text(f"⚠️ **فشل الاتصال بـ Supabase! تفاصيل الخطأ:**\n\n`{str(e)}`", parse_mode="Markdown")
            return
        
        if not files_list:
            await update.message.reply_text(f"⚠️ لا توجد ملفات مرفوعة حالياً في هذا القسم.")
            return

        for f in files_list:
            caption_text = f"📄 {f['file_name']}"
            if f.get("reciter_name"):
                caption_text += f"\n🎙️ بصوت القارئ: {f['reciter_name']}"
                
            if f.get("file_id"):
                if matched_category_code in ["hadith_audio", "quran_audio"]:
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f["file_id"], caption=caption_text)
                else:
                    await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=caption_text)
            elif f.get("file_url"):
                if matched_category_code in ["hadith_audio", "quran_audio"]:
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f["file_url"], caption=caption_text)
                else:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{caption_text}\n🔗 رابط مباشر للتحميل: {f['file_url']}")
        return

    await update.message.reply_text("ℹ️ من فضلك، استخدم أزرار القائمة السفلية الظاهرة أمامك للتنقل.", reply_markup=get_main_keyboard())

# --- الدالة المشغلة للبوت ---
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO, catch_file_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("🤖 Bot is running perfectly with loose text matching!")
    
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 System stopped.")
    
