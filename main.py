import os
import asyncio
from datetime import datetime
from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
# استيراد مكتبة الاتصال بـ Supabase
from supabase import create_client, Client

# --- المتغيرات البيئية وبيانات الربط المستخرجة من الصورة ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
YOUR_TELEGRAM_USERNAME = "Yousef55641" 

# جلب رابط الاستضافة التلقائي من Railway لتشغيل نافذة العداد التنازلي المدمجة
PUBLIC_URL = os.environ.get("RAILWAY_STATIC_URL", "")
if PUBLIC_URL and not PUBLIC_URL.startswith("https://"):
    PUBLIC_URL = f"https://{PUBLIC_URL}"

# 🔥 تم وضع البيانات الحقيقية من صورتك هنا بدقة 100%
SUPABASE_URL = "https://syrpxdwypyisvlmwmmbu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc2MiOiJzdXBhYmFzZSIsInJlZiI6InN5cnB4ZHd5cHlpc3ZsbXdtbWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3M0A5MjE2MDEsImV4cCI6MjA1NzYwOTYwMH0.kG2PzNGb3ta9vu58gZrkCYZj0YTk3VhsNTa-6fiUZ3M"

# تهيئة عميل الاتصال بقاعدة البيانات السحابية للموقع
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- المصفوفات الثابتة للمواد والتصنيفات مطابقة للموقع ---
SUBJECTS = {
    "math": "📐 الرياضيات",
    "phys": "⚡ الفيزياء",
    "chem": "🧪 الكيمياء",
    "science": "🧬 العلوم",
    "islamic": "🕌 التربية الإسلامية",
    "arabic": "📚 اللغة العربية",
    "english": "🇬🇧 اللغة الإنجليزية",
    "french": "🇫🇷 اللغة الفرنسية",
}

CATEGORIES = {
    "book": "📖 الكتاب المدرسي",
    "notes": "📝 الملخصات",
    "notebook": "📒 النوط",
    "remarks": "💡 ملاحظات",
    "exams_year": "📅 أسئلة السنوات (حسب السنة)",
    "exams_all": "📝 أسئلة السنوات (كاملة)",
    "exams_topic": "🔍 أسئلة السنوات (حسب البحث)",
    "hadith_audio": "🔊 الأحاديث بشكل صوتي",
    "quran_audio": "🔊 الآيات بشكل صوتي"
}

# --- صفحة العداد التنازلي للنافذة المنبثقة WebApp (تأخذ التاريخ من الموقع) ---
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
        body {
            margin: 0; padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: #ffffff;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            min-height: 100vh; text-align: center;
        }
        .container {
            width: 90%; max-width: 450px;
            background: rgba(255, 255, 255, 0.06);
            padding: 25px; border-radius: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(12px);
            border: 1px rgba(255, 255, 255, 0.1) solid;
        }
        h1 { font-size: 1.7rem; margin-bottom: 5px; color: #38bdf8; }
        .subtitle { font-size: 0.9rem; color: #94a3b8; margin-bottom: 25px; }
        .countdown-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 25px; }
        .time-box { background: rgba(15, 23, 42, 0.7); padding: 12px 5px; border-radius: 14px; border: 1px rgba(56, 189, 248, 0.2) solid; }
        .time-val { font-size: 1.6rem; font-weight: bold; color: #f8fafc; display: block; }
        .time-lbl { font-size: 0.75rem; color: #38bdf8; }
        .progress-container { background: #334155; border-radius: 10px; height: 12px; width: 100%; overflow: hidden; margin-bottom: 10px; }
        .progress-bar { background: linear-gradient(90deg, #38bdf8, #0ea5e9); height: 100%; width: 0%; transition: width 1s ease; }
        .progress-text { font-size: 0.8rem; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⏳ العداد التنازلي للامتحانات</h1>
        <div class="subtitle">شحذ الهمم يا بطل دورتنا لعام 2026 اقتربت</div>
        <div class="countdown-grid">
            <div class="time-box"><span class="time-val" id="days">00</span><span class="time-lbl">يوم</span></div>
            <div class="time-box"><span class="time-val" id="hours">00</span><span class="time-lbl">ساعة</span></div>
            <div class="time-box"><span class="time-val" id="minutes">00</span><span class="time-lbl">دقيقة</span></div>
            <div class="time-box"><span class="time-val" id="seconds">00</span><span class="time-lbl">ثانية</span></div>
        </div>
        <div class="progress-container"><div class="progress-bar" id="pbar"></div></div>
        <div class="progress-text" id="ptext">جاري الحساب...</div>
    </div>
    <script>
        const targetDate = new Date("__TARGET_DATE__T00:00:00").getTime();
        const startDate = new Date("2025-09-01").getTime();
        function updateTimer() {
            const now = new Date().getTime();
            const diff = targetDate - now;
            if (diff <= 0) {
                document.getElementById("days").innerText = "00";
                document.getElementById("hours").innerText = "00";
                document.getElementById("minutes").innerText = "00";
                document.getElementById("seconds").innerText = "00";
                document.getElementById("pbar").style.width = "100%";
                document.getElementById("ptext").innerText = "بدأت الامتحانات الرسمية! بالتوفيق للجميع 🎯";
                return;
            }
            const d = Math.floor(diff / (1000 * 60 * 60 * 24));
            const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const s = Math.floor((diff % (1000 * 60)) / 1000);
            document.getElementById("days").innerText = d.toString().padStart(2, '0');
            document.getElementById("hours").innerText = h.toString().padStart(2, '0');
            document.getElementById("minutes").innerText = m.toString().padStart(2, '0');
            document.getElementById("seconds").innerText = s.toString().padStart(2, '0');
            const total = targetDate - startDate;
            const passed = now - startDate;
            let pct = Math.min(Math.max(Math.floor((passed / total) * 100), 0), 100);
            document.getElementById("pbar").style.width = pct + "%";
            document.getElementById("ptext").innerText = "مؤشر تقدم رحلة السنة الدراسية: " + pct + "%";
        }
        setInterval(updateTimer, 1000);
        updateTimer();
    </script>
</body>
</html>"""
    html_content = html_content.replace("__TARGET_DATE__", exam_date_str)
    return web.Response(text=html_content, content_type='text/html')

# --- تسجيل المستخدم في الموقع تلقائياً لتحديث الإحصائيات ---
def register_student_to_supabase(user):
    try:
        supabase.table("students").upsert({
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }, on_conflict="telegram_id").execute()
    except Exception as e:
        print(f"Error registering student: {e}")

# --- عرض القائمة الرئيسية للبوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_student_to_supabase(update.effective_user)
    
    keyboard = [
        [KeyboardButton("📢 طلب إعلان"), KeyboardButton("📚 تصفح المكتبة التعليمية")],
        [KeyboardButton("🏠 الرئيسية")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="اختر ما تريده من المكتبة...")
    
    await update.effective_message.reply_text(
        "👋 أهلاً بك في *بوت المكتبة التعليمية* المطور لطلاب البكالوريا العلمية.\n\n"
        "يسعدنا مساعدتك في رحلتك الدراسية، يرجى تصفح الأقسام والمواد المتاحة عبر الأزرار أدناه بكل سهولة:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- معالجة الأزرار النصية السفلية للبوت ---
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    
    if user_text == "🏠 الرئيسية":
        await start(update, context)
        return

    elif user_text == "📚 تصفح المكتبة التعليمية":
        webapp_url = f"{PUBLIC_URL}/countdown" if PUBLIC_URL else "https://google.com"
        keyboard = [
            [InlineKeyboardButton("⏳ العداد التنازلي للامتحانات", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton("📚 عرض المواد الدراسية وملفاتها", callback_data="bac_subjects")]
        ]
        await update.message.reply_text(
            "📚 *أهلاً بك في فروع المكتبة الشاملة*\n\nاختر الخدمة المطلوبة من القائمة الذكية المرتبطة بالموقع الإلكتروني فوراً:", 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown"
        )
        return

    elif user_text == "📢 طلب إعلان":
        keyboard = [[InlineKeyboardButton("💬 تواصل مع إدارة المكتبة", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]]
        await update.message.reply_text(
            "📢 يمكنك طلب نشر إعلانك التعليمي لطلاب البكالوريا عبر البوت.\n\nاضغط على الزر أدناه لإرسال التفاصيل للإدارة لمراجعتها من موقع الإدارة:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

# --- معالجة الضغط على أزرار التصفح الشجرية وجلبها من السيرفر والموقع ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # عرض المواد الدراسية
    if data == "bac_subjects":
        keyboard = []
        sub_keys = list(SUBJECTS.keys())
        for i in range(0, len(sub_keys), 2):
            row = [
                InlineKeyboardButton(SUBJECTS[sub_keys[i]], callback_data=f"sub_{sub_keys[i]}"),
                InlineKeyboardButton(SUBJECTS[sub_keys[i+1]], callback_data=f"sub_{sub_keys[i+1]}") if i+1 < len(sub_keys) else None
            ]
            keyboard.append([b for b in row if b is not None])
        await query.edit_message_text("📚 *اختر المادة الدراسية لفتح رفوف ملفاتها المرفوعة من موقع الإدارة:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # تصفح أقسام المادة المحددة
    elif data.startswith("sub_") and not data.startswith("subcat_"):
        subject_code = data.replace("sub_", "")
        subject_name = SUBJECTS[subject_code]
        
        keyboard = [
            [InlineKeyboardButton("📖 الكتاب المدرسي", callback_data=f"subcat_{subject_code}_book")],
            [InlineKeyboardButton("📝 الملخصات", callback_data=f"subcat_{subject_code}_notes")],
            [InlineKeyboardButton("📒 النوط", callback_data=f"subcat_{subject_code}_notebook")],
            [InlineKeyboardButton("💡 ملاحظات تذكيرية", callback_data=f"subcat_{subject_code}_remarks")],
        ]
        
        if subject_code == "islamic":
            keyboard.append([InlineKeyboardButton("🔊 الأحاديث بشكل صوتي", callback_data="audio_reciters_hadith_audio")])
            keyboard.append([InlineKeyboardButton("🔊 الآيات بشكل صوتي", callback_data="audio_reciters_quran_audio")])
            
        keyboard.append([InlineKeyboardButton("📂 أسئلة السنوات السابقة", callback_data=f"exmenu_{subject_code}")])
        keyboard.append([InlineKeyboardButton("🔙 العودة لرفوف المواد", callback_data="bac_subjects")])
        await query.edit_message_text(f"📂 مكتبة مادة *{subject_name}*\n\nاختر التصنيف المفرز لتصفح المستندات الحالية السحابية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # أسئلة السنوات
    elif data.startswith("exmenu_"):
        subject_code = data.replace("exmenu_", "")
        subject_name = SUBJECTS[subject_code]
        keyboard = [
            [InlineKeyboardButton("📅 حسب السنة", callback_data=f"subcat_{subject_code}_exams_year")],
            [InlineKeyboardButton("📝 كاملة الشرح", callback_data=f"subcat_{subject_code}_exams_all")],
            [InlineKeyboardButton("🔍 حسب الأبحاث", callback_data=f"subcat_{subject_code}_exams_topic")],
            [InlineKeyboardButton("🔙 العودة للمادة", callback_data=f"sub_{subject_code}")]
        ]
        await query.edit_message_text(f"📂 أسئلة سنوات مادة *{subject_name}*\n\nاختر نوع الفرز المطلوب:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # جلب الصوتيات وفرز الشيوخ والقراء من الموقع
    elif data.startswith("audio_reciters_"):
        cat_type = data.replace("audio_reciters_", "")
        
        response = supabase.table("materials").select("reciter_name").eq("subject", "islamic").eq("category", cat_type).execute()
        reciters_data = response.data if response else []
        
        keyboard = [[InlineKeyboardButton("🔙 عودة لمادة الإسلامية", callback_data="sub_islamic")]]
        
        if not reciters_data:
            await query.edit_message_text("⚠️ لا توجد ملفات صوتية مرفوعة من موقع الإدارة في هذا قسم حالياً.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        reciters = set([f.get("reciter_name") for f in reciters_data if f.get("reciter_name")])
        reciter_keyboard = []
        for r in reciters:
            reciter_keyboard.append([InlineKeyboardButton(f"🎙️ القارئ: {r}", callback_data=f"viewaudio_{cat_type}_{r}")])
        reciter_keyboard.append([InlineKeyboardButton("🔙 عودة لمادة الإسلامية", callback_data="sub_islamic")])
        await query.edit_message_text("🎙️ *قائمة القراء والمسموعات المتوفرة في الموقع:*", reply_markup=InlineKeyboardMarkup(reciter_keyboard), parse_mode="Markdown")

    # تشغيل وإرسال الصوت المختار
    elif data.startswith("viewaudio_"):
        parts = data.split("_", 2)
        cat_type = parts[1]
        reciter_name = parts[2]
        
        response = supabase.table("materials").select("*").eq("subject", "islamic").eq("category", cat_type).eq("reciter_name", reciter_name).execute()
        files_list = response.data if response.data else []
        
        await query.message.reply_text(f"⏳ جاري سحب المسموعات بصوت القارئ: {reciter_name} من خادم الموقع المطور...")
        for f in files_list:
            if f.get("file_id"):
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f["file_id"], caption=f"🎵 {f['file_name']}")
            elif f.get("file_url"):
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f["file_url"], caption=f"🎵 {f['file_name']}")

    # جلب وإرسال المستندات والكتب والملخصات المرفوعة من الموقع تلقائياً
    elif data.startswith("subcat_"):
        parts = data.split("_", 2)
        subject_code = parts[1]
        cat_type = parts[2]
        
        response = supabase.table("materials").select("*").eq("subject", subject_code).eq("category", cat_type).execute()
        files_list = response.data if response.data else []
        
        keyboard = [[InlineKeyboardButton("🔙 عودة للمادة", callback_data=f"sub_{subject_code}")]]
        if not files_list:
            cat_name = CATEGORIES.get(cat_type, cat_type)
            await query.edit_message_text(f"⚠️ لا توجد ملفات مرفوعة حالياً من الموقع في قسم: *{cat_name}*.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
            
        await query.message.reply_text("⏳ جاري جلب المستندات والروابط التعليمية المحدثة من الموقع...")
        for f in files_list:
            if f.get("file_id"):
                await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=f"📄 {f['file_name']}")
            elif f.get("file_url"):
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"📄 *{f['file_name']}*\n🔗 رابط الملف المباشر: {f['file_url']}", parse_mode="Markdown")

# --- الدالة المشغلة المتزامنة للبوت وخادم الويب المدمج ---
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    web_app = web.Application()
    web_app.router.add_get('/countdown', countdown_page)
    
    port = int(os.environ.get("PORT", "8080"))
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    await site.start()
    print(f"🌍 WebApp is serving countdown at port {port}")

    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        print("🤖 Educational Library Bot is now successfully connected to the Database & Telegram servers!")
        
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 System stopped.")
            
