import os
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from supabase import create_client, Client

# --- إعداد السجلات ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- المتغيرات ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
YOUR_TELEGRAM_USERNAME = "Yousef55641" 
SUPABASE_URL = "https://syrpxdwypyisvlmwmmbu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN5cnB4ZHd5cHlpc3ZsbXdtbWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MjE2MDEsImV4cCI6MjA5NjQ5NzYwMX0.kG2PzNGb3ta9vu58gZrkCYZJ0YTk3VhsNTa-6fiUZ3M"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SUBJECTS = {
    "📐 الرياضيات": "math",
    "🧲 الفيزياء": "phys",
    "🧪 الكيمياء": "chem",
    "🧬 العلوم": "science",
    "🕋 التربية الإسلامية": "islamic",
    "📚 اللغة العربية": "arabic",
    "🇬🇧 اللغة الإنجليزية": "english",
    "🇫🇷 اللغة الفرنسية": "french",
}

# --- نظام الإعلانات التلقائي ---
async def broadcast_announcement(context: ContextTypes.DEFAULT_TYPE):
    try:
        response = supabase.table("announcements").select("*").eq("is_sent", False).execute()
        announcements = response.data
        if not announcements:
            return

        students = supabase.table("students").select("telegram_id").execute()
        student_ids = [s['telegram_id'] for s in students.data]

        for ann in announcements:
            msg = ann['message']
            for chat_id in student_ids:
                try:
                    await context.bot.send_message(chat_id=chat_id, text=f"📢 <b>إعلان هام من المكتبة:</b>\n\n{msg}", parse_mode="HTML")
                    await asyncio.sleep(0.05)
                except Exception:
                    continue
            supabase.table("announcements").update({"is_sent": True}).eq("id", ann['id']).execute()
            logger.info(f"تم بث الإعلان رقم {ann['id']} بنجاح.")
    except Exception as e:
        logger.error(f"Error broadcasting: {e}")

# --- الدوال المساعدة السابقة ---
async def register_student_to_supabase(user):
    try:
        await asyncio.to_thread(
            lambda: supabase.table("students").upsert({
                "telegram_id": user.id, "username": user.username, "first_name": user.first_name
            }, on_conflict="telegram_id").execute()
        )
    except Exception as e:
        logger.error(f"Error registering student: {e}")

async def catch_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        f_id = update.message.document.file_id
        await update.message.reply_text(f"📄 معرف الملف:\n<code>{f_id}</code>", parse_mode="HTML")
    elif update.message.audio:
        f_id = update.message.audio.file_id
        await update.message.reply_text(f"🔊 معرف الملف الصوتي:\n<code>{f_id}</code>", parse_mode="HTML")

async def send_secured_document(context, chat_id, f_id, f_url, caption_text):
    try:
        if f_id:
            await context.bot.send_document(chat_id=chat_id, document=f_id, caption=caption_text, parse_mode="HTML")
            return True
    except Exception as e:
        logger.warning(f"File ID failed: {e}")
    try:
        if f_url:
            await context.bot.send_document(chat_id=chat_id, document=f_url, caption=caption_text, parse_mode="HTML")
            return True
    except Exception as e:
        logger.error(f"URL failed: {e}")
    if f_url:
        await context.bot.send_message(chat_id=chat_id, text=f"📄 <b>{caption_text}</b>\n\n🔗 الرابط: {f_url}", parse_mode="HTML")
        return True
    return False

# --- الكيبوردات ---
def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("البكلوريا العلمي 🎓")],
        [KeyboardButton("📢 طلب إعلان للمكتبة"), KeyboardButton("💬 تواصل مع الإدارة")]
    ], resize_keyboard=True)

def get_subjects_keyboard():
    return ReplyKeyboardMarkup([
        ["🧲 الفيزياء", "📐 الرياضيات"],
        ["🧬 العلوم", "🧪 الكيمياء"],
        ["📚 اللغة العربية", "🕋 التربية الإسلامية"],
        ["🇫🇷 اللغة الفرنسية", "🇬🇧 اللغة الإنجليزية"],
        ["📅 برنامج الامتحان"],
        ["🔙 العودة للقائمة الرئيسية"]
    ], resize_keyboard=True)

def get_categories_keyboard(subject_name):
    keyboard = [
        ["📝 الملخصات الذهنية", "📖 الكتاب المدرسي"],
        ["💡 ملاحظات تذكيرية", "📒 النوط الشاملة"],
        ["📂 أسئلة السنوات السابقة"]
    ]
    if "الإسلامية" in subject_name or "🕋" in subject_name:
        keyboard.insert(2, ["🔊 الأحاديث الشريفة", "🔊 الآيات القرآنية"])
    keyboard.append(["🔙 تغيير المادة المحددة"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_exams_keyboard():
    return ReplyKeyboardMarkup([["📅 حسب السنة", "📝 كاملة"], ["🔍 حسب الأبحاث"], ["🔙 العودة لأقسام المادة"]], resize_keyboard=True)

# --- معالجة المنطق ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await register_student_to_supabase(update.effective_user)
    context.user_data.clear() 
    await update.effective_message.reply_text("👋 أهلاً بك في بوت المكتبة التعليمية.", reply_markup=get_main_keyboard())

async def handle_bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    if "العودة للقائمة الرئيسية" in text:
        user_data.clear()
        await update.message.reply_text("🔙 الرئيسية:", reply_markup=get_main_keyboard())
        return

    # ميزة برنامج الامتحان الجديدة
    if "📅 برنامج الامتحان" in text:
        res = await asyncio.to_thread(lambda: supabase.table("materials").select("*").eq("category", "exams_schedule").execute())
        if res.data:
            for f in res.data:
                await send_secured_document(context, update.effective_chat.id, f.get("file_id"), f.get("file_url"), f"📅 {f.get('name')}")
        else:
            await update.message.reply_text("⚠️ لم يتم رفع برنامج الامتحان بعد.")
        return

    elif "البكلوريا العلمي" in text or "تغيير المادة" in text:
        await update.message.reply_text("📚 اختر المادة:", reply_markup=get_subjects_keyboard())
        return

    # منطق الصوتيات (يجب الحفاظ عليه)
    if "audio_files" in user_data and "active_audio_category" in user_data:
        audio_files = user_data["audio_files"]
        for f in audio_files:
            r_name = f.get("reciter_name") or f.get("reciter") or "قارئ عام"
            if text == f"🎙️ {r_name}":
                f_id = f.get("file_id") or f.get("telegram_file_id")
                f_url = f.get("file_url") or f.get("url")
                if f.get("category") in ["hadith_audio", "quran_audio"]:
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f_id or f_url, caption=f"📎 {f.get('name')}")
        return

    # منطق المواد والتصنيفات
    matched_subject = next((k for k in SUBJECTS.keys() if k.replace("📐","").replace("🧲","").replace("🧪","").replace("🧬","").replace("🕋","").replace("📚","").replace("🇬🇧","").replace("🇫🇷","").strip() in text), None)
    
    if matched_subject:
        user_data["current_subject_name"] = matched_subject
        user_data["current_subject_code"] = SUBJECTS[matched_subject]
        await update.message.reply_text(f"✨ مادة: {matched_subject}", reply_markup=get_categories_keyboard(matched_subject))
        return

    # خريطة التصنيفات
    cat_map = {"حسب السنة": "exams_year", "كاملة": "exams_full", "حسب الأبحاث": "exams_topic", "الملخصات الذهنية": "summaries", "الكتاب المدرسي": "textbook", "النوط الشاملة": "booklets", "ملاحظات تذكيرية": "notes", "الأحاديث الشريفة": "hadith_audio", "الآيات القرآنية": "quran_audio"}
    matched_cat = next((v for k, v in cat_map.items() if k in text), None)

    if matched_cat and "current_subject_code" in user_data:
        files = supabase.table("materials").select("*").eq("subject", user_data["current_subject_code"]).eq("category", matched_cat).execute().data
        if not files:
            await update.message.reply_text("⚠️ لا توجد ملفات.")
            return
        for f in files:
            await send_secured_document(context, update.effective_chat.id, f.get("file_id"), f.get("file_url"), f"📄 {f.get('name')}")
        return

    await update.message.reply_text("استخدم القائمة السفلية.", reply_markup=get_main_keyboard())

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # تشغيل الإعلانات كل ساعة
    application.job_queue.run_repeating(broadcast_announcement, interval=3600, first=10)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO, catch_file_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))

    logger.info("🚀 البوت يعمل.")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
