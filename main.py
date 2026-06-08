import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from supabase import create_client, Client

# --- المتغيرات البيئية وبيانات الربط ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
YOUR_TELEGRAM_USERNAME = "Yousef55641" 

SUPABASE_URL = "https://syrpxdwypyisvlmwmmbu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInT5cCI6IkpXVCJ9.eyJpc2MiOiJzdXBhYmFzZSIsInJlZiI6InN5cnB4ZHd5cHlpc3ZsbXdtbWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3M0A5MjE2MDEsImV4cCI6MjA1NzYwOTYwMH0.kG2PzNGb3ta9vu58gZrkCYZj0YTk3VhsNTa-6fiUZ3M"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 🌟 المواد بالأسماء العربية والرموز الأيقونية الفخمة 🌟 ---
SUBJECTS = {
    "الرياضيات 📐": "math",
    "الفيزياء 🌀": "phys",
    "الكيمياء ⚗️": "chem",
    "علم الأحياء 🔬": "science",
    "التربية الإسلامية 🕋": "islamic",
    "اللغة العربية 📚": "arabic",
    "اللغة الإنجليزية 🔤": "english",
    "اللغة الفرنسية 🗼": "french",
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

# --- لوحات المفاتيح السفلية المنسقة هندسياً ---
def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("البكلوريا العلمي 🔬"), KeyboardButton("📢 طلب إعلان للمكتبة")],
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

# --- ميزة التقاط معرفات الملفات تلقائياً (File ID Catcher) ---
async def catch_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        f_id = update.message.document.file_id
        await update.message.reply_text(
            f"📄 **تم التقاط معرف المستند بنجاح!**\n\n"
            f"اضغط عليه للنسخ فوراً:\n`{f_id}`", 
            parse_mode="Markdown"
        )
    elif update.message.audio:
        f_id = update.message.audio.file_id
        await update.message.reply_text(
            f"🔊 **تم التقاط معرف الملف الصوتي بنجاح!**\n\n"
            f"اضغط عليه للنسخ فوراً:\n`{f_id}`", 
            parse_mode="Markdown"
        )

# --- منطق معالجة الرسائل المستقر والقوي كلياً ---
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

    if text in ["🔙 العودة للقائمة الرئيسية", "🏠 الرئيسية"]:
        user_data.clear()
        await update.message.reply_text("🔙 تم العودة للقائمة الرئيسية للخدمات:", reply_markup=get_main_keyboard())
        return

    elif text in ["البكلوريا العلمي 🔬", "🗂️ تصفح المواد الدراسية", "📚 تصفح المواد الدراسية", "🔙 تغيير المادة المحددة"]:
        await update.message.reply_text("✨ **يرجى اختيار المادة المطلوبة من القائمة الأيقونية المحدثة:**", reply_markup=get_subjects_keyboard(), parse_mode="Markdown")
        return

    elif text in ["📢 طلب إعلان للمكتبة", "💬 تواصل مع الإدارة"]:
        await update.message.reply_text(f"💬 يمكنك التواصل مباشرة مع إدارة المكتبة والموقع عبر الحساب الرسمي التالي:\n\n🔗 @{YOUR_TELEGRAM_USERNAME}")
        return

    # التحقق الديناميكي من اختيار المادة
    if text in SUBJECTS:
        user_data["current_subject_name"] = text
        user_data["current_subject_code"] = SUBJECTS[text]
        await update.message.reply_text(f"✨ لقد فتحت الآن رفوف مادة:\n🎯 *{text}*\n\nيرجى تحديد التصنيف المراد عرضه من الأزرار بالأسفل:", reply_markup=get_categories_keyboard(text), parse_mode="Markdown")
        return

    # دخول أرشيف أسئلة السنوات
    if text == "📂 أسئلة السنوات السابقة":
        if "current_subject_code" not in user_data:
            await update.message.reply_text("⚠️ يرجى اختيار المادة أولاً.", reply_markup=get_subjects_keyboard())
            return
        await update.message.reply_text("📅 اختر طريقة عرض الفرز لأسئلة السنوات السابقة:", reply_markup=get_exams_keyboard())
        return

    # العودة لأقسام المادة
    if text == "🔙 العودة لأقسام المادة":
        if "current_subject_name" not in user_data:
            await update.message.reply_text("⚠️ انتهت الجلسة، يرجى إعادة اختيار المادة:", reply_markup=get_subjects_keyboard())
            return
        subject_name = user_data["current_subject_name"]
        await update.message.reply_text(f"📂 تم العودة لقائمة أقسام مادة:\n🎯 *{subject_name}*", reply_markup=get_categories_keyboard(subject_name), parse_mode="Markdown")
        return

    # جلب ومعالجة المحتويات من قاعدة البيانات فوراً
    if text in CATEGORIES or text in ["📅 حسب السنة", "📝 كاملة الشرح", "🔍 حسب الأبحاث"]:
        if "current_subject_code" not in user_data:
            await update.message.reply_text("⚠️ انتهت الجلسة، يرجى إعادة اختيار المادة:", reply_markup=get_subjects_keyboard())
            return
        
        cat_map = {
            "📅 حسب السنة": "exams_year",
            "📝 كاملة الشرح": "exams_all",
            "🔍 حسب الأبحاث": "exams_topic"
        }
        category_code = cat_map.get(text, CATEGORIES.get(text))
        subject_code = user_data["current_subject_code"]
        
        await update.message.reply_text("⏳ جاري سحب المستندات والملفات المحدثة من سيرفر الموقع...")
        
        # 🌟 تعديل هنا لطرد نص الخطأ الحقيقي ومعرفته 🌟
        try:
            response = supabase.table("materials").select("*").eq("subject", subject_code).eq("category", category_code).execute()
            files_list = response.data if response.data else []
        except Exception as e:
            await update.message.reply_text(f"⚠️ **فشل الاتصال بـ Supabase! تفاصيل الخطأ البرمجي:**\n\n`{str(e)}`", parse_mode="Markdown")
            return
        
        if not files_list:
            await update.message.reply_text(f"⚠️ لا توجد ملفات مرفوعة حالياً في هذا القسم.")
            return

        for f in files_list:
            caption_text = f"📄 {f['file_name']}"
            if f.get("reciter_name"):
                caption_text += f"\n🎙️ بصوت القارئ: {f['reciter_name']}"
                
            if f.get("file_id"):
                if category_code in ["hadith_audio", "quran_audio"]:
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f["file_id"], caption=caption_text)
                else:
                    await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=caption_text)
            elif f.get("file_url"):
                if category_code in ["hadith_audio", "quran_audio"]:
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f["file_url"], caption=caption_text)
                else:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{caption_text}\n🔗 رابط مباشر للتحميل: {f['file_url']}")
        return

    await update.message.reply_text("ℹ️ من فضلك، استخدم أزرار القائمة السفلية الظاهرة أمامك للتنقل.", reply_markup=get_main_keyboard())

# --- الدالة المشغلة المتزامنة الكاملة والآمنة برمجياً ---
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO, catch_file_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("🤖 Educational Library Bot is now running perfectly!")
    
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
        
