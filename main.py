import os
import asyncio
from datetime import datetime
from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from supabase import create_client, Client

# --- المتغيرات البيئية وبيانات الربط المستخرجة ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
YOUR_TELEGRAM_USERNAME = "Yousef55641" 

# سحب المنفذ والروابط من السيرفر تلقائياً وبأعلى دقة لمنع خطأ الـ Not Found
PORT = int(os.environ.get("PORT", "8080"))
RAILWAY_URL = os.environ.get("RAILWAY_PUBLIC_URL", os.environ.get("RAILWAY_STATIC_URL", ""))

if RAILWAY_URL:
    if not RAILWAY_URL.startswith("http://") and not RAILWAY_URL.startswith("https://"):
        PUBLIC_URL = f"https://{RAILWAY_URL}"
    else:
        PUBLIC_URL = RAILWAY_URL
else:
    # حل بديل ذكي في حال لم تتوفر المتغيرات تلقائياً
    PUBLIC_URL = "https://sina-bot-production.up.railway.app"

SUPABASE_URL = "https://syrpxdwypyisvlmwmmbu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc2MiOiJzdXBhYmFzZSIsInJlZiI6InN5cnB4ZHd5cHlpc3ZsbXdtbWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3M0A5MjE2MDEsImV4cCI6MjA1NzYwOTYwMH0.kG2PzNGb3ta9vu58gZrkCYZj0YTk3VhsNTa-6fiUZ3M"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- المصفوفات الثابتة للمواد بالأيقونات والأسماء المطابقة للتصميم الجديد ---
SUBJECTS = {
    "📐 الرياضيات": "math",
    "⚡ الفيزياء": "phys",
    "🧪 الكيمياء": "chem",
    "🧬 العلوم": "science",
    "🕌 التربية الإسلامية": "islamic",
    "📚 اللغة العربية": "arabic",
    "🇬🇧 اللغة الإنجليزية": "english",
    "🇫🇷 اللغة الفرنسية": "french",
}

CATEGORIES = {
    "📖 الكتاب المدرسي": "book",
    "📝 الملخصات": "notes",
    "📒 النوط": "notebook",
    "💡 ملاحظات تذكيرية": "remarks",
    "📅 أسئلة السنوات (حسب السنة)": "exams_year",
    "📝 أسئلة السنوات (كاملة)": "exams_all",
    "🔍 أسئلة السنوات (حسب البحث)": "exams_topic",
    "🔊 الأحاديث بشكل صوتي": "hadith_audio",
    "🔊 الآيات بشكل صوتي": "quran_audio"
}

# --- صفحة العداد التنازلي المصممة برمجياً للنافذة المنبثقة WebApp ---
async def countdown_page(request):
    try:
        response = supabase.table("settings").select("value").eq("key", "exam_date").execute()
        exam_date_str = response.data[0]["value"] if response.data else "2026-06-15"
    except Exception:
        exam_date_str = "2026-06-15"
    
    html_content = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مؤقت الامتحانات الوزارية</title>
    <style>
        body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, sans-serif; background: linear-gradient(135deg, #0b0f19, #111827); color: #ffffff; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; text-align: center; }
        .container { width: 90%; max-width: 420px; background: rgba(255, 255, 255, 0.04); padding: 30px 20px; border-radius: 28px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6); backdrop-filter: blur(16px); border: 1px rgba(56, 189, 248, 0.15) solid; }
        h1 { font-size: 1.6rem; margin-bottom: 5px; color: #38bdf8; text-shadow: 0 2px 10px rgba(56,189,248,0.3); }
        .subtitle { font-size: 0.85rem; color: #94a3b8; margin-bottom: 30px; }
        .countdown-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 10px; }
        .time-box { background: #0f172a; padding: 15px 5px; border-radius: 16px; border: 1px rgba(255, 255, 255, 0.05) solid; box-shadow: inset 0 2px 8px rgba(0,0,0,0.5); }
        .time-val { font-size: 1.8rem; font-weight: bold; color: #38bdf8; display: block; font-variant-numeric: tabular-nums; }
        .time-lbl { font-size: 0.75rem; color: #64748b; margin-top: 4px; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⏳ الامتحانات الوزارية 2026</h1>
        <div class="subtitle">شحذ الهمم يا بطل، متبقي على حلمك الممتد:</div>
        <div class="countdown-grid">
            <div class="time-box"><span class="time-val" id="days">00</span><span class="time-lbl">الأيام</span></div>
            <div class="time-box"><span class="time-val" id="hours">00</span><span class="time-lbl">الساعات</span></div>
            <div class="time-box"><span class="time-val" id="minutes">00</span><span class="time-lbl">الدقائق</span></div>
            <div class="time-box"><span class="time-val" id="seconds">00</span><span class="time-lbl">الثواني</span></div>
        </div>
    </div>
    <script>
        const targetDate = new Date("__TARGET_DATE__T00:00:00").getTime();
        function updateTimer() {
            const now = new Date().getTime();
            const diff = targetDate - now;
            if (diff <= 0) {
                document.getElementById("days").innerText = "00";
                document.getElementById("hours").innerText = "00";
                document.getElementById("minutes").innerText = "00";
                document.getElementById("seconds").innerText = "00";
                return;
            }
            document.getElementById("days").innerText = Math.floor(diff / (1000 * 60 * 60 * 24)).toString().padStart(2, '0');
            document.getElementById("hours").innerText = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)).toString().padStart(2, '0');
            document.getElementById("minutes").innerText = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)).toString().padStart(2, '0');
            document.getElementById("seconds").innerText = Math.floor((diff % (1000 * 60)) / 1000).toString().padStart(2, '0');
        }
        setInterval(updateTimer, 1000);
        updateTimer();
    </script>
</body>
</html>"""
    html_content = html_content.replace("__TARGET_DATE__", exam_date_str)
    return web.Response(text=html_content, content_type='text/html')

def register_student_to_supabase(user):
    try:
        supabase.table("students").upsert({"telegram_id": user.id, "username": user.username, "first_name": user.first_name}, on_conflict="telegram_id").execute()
    except Exception as e:
        print(f"Error registering student: {e}")

# --- لوحات المفاتيح السفلية الذكية بالأيقونات الجديدة الجذابة ---
def get_main_keyboard():
    webapp_url = f"{PUBLIC_URL}/countdown"
    return ReplyKeyboardMarkup([
        [KeyboardButton("⏳ العداد التنازلي", web_app=WebAppInfo(url=webapp_url)), KeyboardButton("📚 تصفح المواد الدراسية")],
        [KeyboardButton("📢 طلب إعلان"), KeyboardButton("💬 تواصل مع الإدارة")]
    ], resize_keyboard=True, input_field_placeholder="القائمة الرئيسية...")

def get_subjects_keyboard():
    keys = list(SUBJECTS.keys())
    return ReplyKeyboardMarkup([
        [keys[0], keys[1]],
        [keys[2], keys[3]],
        [keys[4], keys[5]],
        [keys[6], keys[7]],
        ["🔙 العودة للقائمة الرئيسية"]
    ], resize_keyboard=True, input_field_placeholder="اختر المادة الدراسية...")

def get_categories_keyboard(subject_name):
    keyboard = [
        ["📖 الكتاب المدرسي", "📝 الملخصات"],
        ["📒 النوط", "💡 ملاحظات تذكيرية"],
        ["📂 أسئلة السنوات السابقة"]
    ]
    if "الإسلامية" in subject_name:
        keyboard.insert(2, ["🔊 الأحاديث بشكل صوتي", "🔊 الآيات بشكل صوتي"])
    keyboard.append(["🔙 تغيير المادة المحددة"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder=f"تصنيفات {subject_name}...")

def get_exams_keyboard():
    return ReplyKeyboardMarkup([
        ["📅 حسب السنة", "📝 كاملة الشرح"],
        ["🔍 حسب الأبحاث"],
        ["🔙 العودة لأقسام المادة"]
    ], resize_keyboard=True, input_field_placeholder="اختر نوع الفرز لأسئلة السنوات...")

# --- منطق معالجة الرسائل والقوائم الشجرية السفلية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_student_to_supabase(update.effective_user)
    context.user_data.clear() 
    
    await update.effective_message.reply_text(
        "👋 أهلاً بك في *بوت المكتبة التعليمية* لطلاب البكالوريا العلمية.\n\n"
        "تم تحديث الأيقونات الرسومية وإصلاح رابط العداد التنازلي بنجاح! يرجى استخدام القائمة السفلية للتصفح السلس والمنظم:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def handle_bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    if text == "🔙 العودة للقائمة الرئيسية" or text == "🏠 الرئيسية":
        user_data.clear()
        await update.message.reply_text("🔙 تم العودة للقائمة الرئيسية للخدمات:", reply_markup=get_main_keyboard())
        return

    elif text == "📚 تصفح المواد الدراسية" or text == "🔙 تغيير المادة المحددة":
        await update.message.reply_text("📚 اختر المادة التي ترغب بتصفح ملفاتها بالأيقونات الرسومية المحدثة الأنيقة:", reply_markup=get_subjects_keyboard())
        return

    elif text == "📢 طلب إعلان" or text == "💬 تواصل مع الإدارة":
        await update.message.reply_text(f"💬 يمكنك التواصل مباشرة مع إدارة المكتبة والموقع عبر الحساب الرسمي التالي:\n\n🔗 @{YOUR_TELEGRAM_USERNAME}")
        return

    # رصد اختيار المادة
    if text in SUBJECTS:
        user_data["current_subject_name"] = text
        user_data["current_subject_code"] = SUBJECTS[text]
        await update.message.reply_text(f"📂 لقد فتحت الآن رفوف مادة: *{text}*\n\nاختر القسم المطلوب من القائمة بالأسفل:", reply_markup=get_categories_keyboard(text), parse_mode="Markdown")
        return

    # أقسام أسئلة السنوات
    if text == "📂 أسئلة السنوات السابقة" or text == "🔙 العودة لأقسام المادة":
        if "current_subject_code" not in user_data:
            await update.message.reply_text("⚠️ يرجى اختيار المادة أولاً.", reply_markup=get_subjects_keyboard())
            return
        await update.message.reply_text("📅 اختر طريقة عرض الفرز لأسئلة السنوات السابقة:", reply_markup=get_exams_keyboard())
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
        
        response = supabase.table("materials").select("*").eq("subject", subject_code).eq("category", category_code).execute()
        files_list = response.data if response.data else []
        
        if not files_list:
            await update.message.reply_text(f"⚠️ لا توجد ملفات مرفوعة حالياً من لوحة تحكم الموقع في هذا القسم (`{text}`).")
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

# --- الدالة المشغلة المتزامنة للبوت وخادم الويب المدمج ---
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))

    web_app = web.Application()
    web_app.router.add_get('/countdown', countdown_page)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌍 WebApp is serving countdown at port {PORT}")

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
        
