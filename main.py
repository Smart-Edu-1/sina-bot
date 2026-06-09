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

# --- المتغيرات البيئية ---
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

# --- دوال مساعدة ---
async def register_student_to_supabase(user):
    try:
        await asyncio.to_thread(
            lambda: supabase.table("students").upsert({
                "telegram_id": user.id, 
                "username": user.username, 
                "first_name": user.first_name
            }, on_conflict="telegram_id").execute()
        )
    except Exception as e:
        logger.error(f"Error registering student: {e}")

async def broadcast_announcement(context: ContextTypes.DEFAULT_TYPE):
    """دالة فحص وإرسال الإعلانات لجميع الطلاب"""
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

async def send_secured_document(context, chat_id, f_id, f_url, caption_text):
    if f_url and f_url.startswith("http"):
        try:
            await context.bot.send_document(chat_id=chat_id, document=f_url, caption=caption_text, parse_mode="HTML")
            return True
        except Exception:
            pass
    if f_id:
        try:
            await context.bot.send_document(chat_id=chat_id, document=f_id, caption=caption_text, parse_mode="HTML")
            return True
        except Exception:
            pass
    await context.bot.send_message(chat_id=chat_id, text=f"📄 {caption_text}\n\n⚠️ تعذر إرسال الملف تلقائياً، الرابط المباشر:\n{f_url}", parse_mode="HTML")
    return False

# --- كيبوردات ---
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

# --- معالجات البوت ---
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

    elif "البكلوريا العلمي" in text or "تغيير المادة" in text:
        await update.message.reply_text("📚 اختر المادة التي ترغب بتصفح ملفاتها:", reply_markup=get_subjects_keyboard())
        return

    # باقي المنطق (تم اختصاره هنا لتوفير المساحة، ضع كودك الأصلي هنا)
    # ... (ضع هنا logic معالجة الملفات والملفات الصوتية كما هي في كودك القديم) ...
    # تذكر: استخدم دالة send_secured_document بدلاً من send_document مباشرة

    await update.message.reply_text("استخدم القائمة السفلية للتنقل.", reply_markup=get_main_keyboard())

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ربط دالة الإعلانات (فحص كل 60 ثانية)
    application.job_queue.run_repeating(broadcast_announcement, interval=60, first=10)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))

    logger.info("🚀 البوت يعمل الآن بكفاءة مع نظام الإعلانات.")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
