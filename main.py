import os
import json
import asyncio
from datetime import datetime
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# --- المتغيرات البيئية ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# تأكد من جعل ADMIN_ID رقماً في إعدادات Railway وليس معرفاً يبدأ بـ @
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
YOUR_TELEGRAM_USERNAME = "Yousef55641" 

# جلب رابط التطبيق التلقائي من Railway لتشغيل نافذة العداد
PUBLIC_URL = os.environ.get("RAILWAY_STATIC_URL", "")
if PUBLIC_URL and not PUBLIC_URL.startswith("https://"):
    PUBLIC_URL = f"https://{PUBLIC_URL}"

DATA_FILE = "bot_data.json"

# --- إدارة البيانات ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "files": {}, "exam_date": "2026-06-15"}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            d = json.load(f)
            if "exam_date" not in d: d["exam_date"] = "2026-06-15"
            return d
        except json.JSONDecodeError:
            return {"users": [], "files": {}, "exam_date": "2026-06-15"}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_user_if_new(user_id):
    data = load_data()
    if "users" not in data: data["users"] = []
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

# --- المواد والتصنيفات ---
SUBJECTS = {
    "math": "📐 الرياضيات",
    "phys": "⚡ الفيزياء",
    "chem": "🧪 الكيمياء",
    "science": "🧬 العلوم",
    "islamic": "🕌 التربية الإسلامية",
    "arabic": "📚 اللغة العربية",
    "english": "🇬🇧 اللغة الإنجليزية",
    "french": "🇫🇷 اللغة الفرنسية",
    "national": "🦅 التربية الوطنية"
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

# --- واجهة العداد التنازلي (HTML/CSS) للنافذة المفتوحة ---
async def countdown_page(request):
    data = load_data()
    exam_date_str = data.get("exam_date", "2026-06-15")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>مؤقت نهاية الامتحان</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0f172a, #1e293b);
                color: #ffffff;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                text-align: center;
            }}
            .container {{
                width: 90%;
                max-width: 500px;
                background: rgba(255, 255, 255, 0.05);
                padding: 30px;
                border-radius: 24px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                border: 1px rgba(255, 255, 255, 0.1) solid;
            }}
            h1 {{
                font-size: 1.8rem;
                margin-bottom: 5px;
                color: #38bdf8;
            }}
            .subtitle {{
                font-size: 0.9rem;
                color: #94a3b8;
                margin-bottom: 30px;
            }}
            .countdown-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px;
                margin-bottom: 30px;
            }}
            .time-box {{
                background: rgba(15, 23, 42, 0.6);
                padding: 15px 5px;
                border-radius: 16px;
                border: 1px rgba(56, 189, 248, 0.2) solid;
            }}
            .time-val {{
                font-size: 1.8rem;
                font-weight: bold;
                color: #f8fafc;
                display: block;
            }}
            .time-lbl {{
                font-size: 0.8rem;
                color: #38bdf8;
            }}
            .progress-container {{
                background: #334155;
                border-radius: 10px;
                height: 12px;
                width: 100%;
                overflow: hidden;
                margin-bottom: 10px;
            }}
            .progress-bar {{
                background: linear-gradient(90deg, #38bdf8, #0ea5e9);
                height: 100%;
                width: 0%;
                transition: width 1s ease;
            }}
            .progress-text {{
                font-size: 0.85rem;
                color: #94a3b8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⏳ مؤقت نهاية الامتحان</h1>
            <div class="subtitle">الآن نقترب من الفرحة النهائية دورتنا لعام 2026</div>
            
            <div class="countdown-grid">
                <div class="time-box"><span class="time-val" id="days">00</span><span class="time-lbl">يوم</span></div>
                <div class="time-box"><span class="time-val" id="hours">00</span><span class="time-lbl">ساعة</span></div>
                <div class="time-box"><span class="time-val" id="minutes">00</span><span class="time-lbl">دقيقة</span></div>
                <div class="time-box"><span class="time-val" id="seconds">00</span><span class="time-lbl">ثانية</span></div>
            </div>

            <div class="progress-container">
                <div class="progress-bar" id="pbar"></div>
            </div>
            <div class="progress-text" id="ptext">مؤشر تقدم رحلة الامتحانات: 0%</div>
        </div>

        <script>
            const targetDate = new Date("{exam_date_str}T00:00:00").getTime();
            const startDate = new Date("2025-09-01").getTime(); // بداية السنة الدراسية كافتراض للحساب

            function updateTimer() {{
                const now = new Date().getTime();
                const diff = targetDate - now;

                if (diff <= 0) {{
                    document.getElementById("days").innerText = "00";
                    document.getElementById("hours").innerText = "00";
                    document.getElementById("minutes").innerText = "00";
                    document.getElementById("seconds").innerText = "00";
                    document.getElementById("pbar").style.width = "100%";
                    document.getElementById("ptext").innerText = "انطلقت الامتحانات! بالتوفيق والنجاح 🎯";
                    return;
                }}

                const d = Math.floor(diff / (1000 * 60 * 60 * 24));
                const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const s = Math.floor((diff % (1000 * 60)) / 1000);

                document.getElementById("days").innerText = d.toString().padStart(2, '0');
                document.getElementById("hours").innerText = h.toString().padStart(2, '0');
                document.getElementById("minutes").innerText = m.toString().padStart(2, '0');
                document.getElementById("seconds").innerText = s.toString().padStart(2, '0');

                // حساب النسبة المئوية للتقدم
                const total = targetDate - startDate;
                const passed = now - startDate;
                let pct = Math.min(Math.max(Math.floor((passed / total) * 100), 0), 100);
                
                document.getElementById("pbar").style.width = pct + "%";
                document.getElementById("ptext").innerText = "مؤشر تقدم رحلة الامتحانات: " + pct + "%";
            }}

            setInterval(updateTimer, 1000);
            updateTimer();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- دالات البوت الأساسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user_if_new(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton("🎓 بكلوريا علمي", callback_data="menu_bac")],
        [InlineKeyboardButton("📢 نشر إعلان", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
    ]
    await update.effective_message.reply_text(
        "👋 أهلاً بك في بوت سينا التعليمي المخصص لطلاب البكالوريا العلمية.\n\nالرجاء الاختيار من القائمة لتبدأ التصفح:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    bot_data = load_data()

    if data == "menu_bac":
        webapp_url = f"{PUBLIC_URL}/countdown" if PUBLIC_URL else "https://google.com"
        keyboard = [
            [InlineKeyboardButton("⏳ تبقى للامتحان (اضغط لفتح النافذة)", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton("📅 برنامج الامتحان", callback_data="bac_schedule")],
            [InlineKeyboardButton("📚 المواد الدراسية", callback_data="bac_subjects")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="menu_main")]
        ]
        await query.edit_message_text("🎓 *قسم البكالوريا العلمية*\n\nاختر وجهتك المطلوبة بدقة:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_main":
        keyboard = [
            [InlineKeyboardButton("🎓 بكلوريا علمي", callback_data="menu_bac")],
            [InlineKeyboardButton("📢 نشر إعلان", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
        ]
        await query.edit_message_text("👋 أهلاً بك مجدداً في بوت سينا التعليمي. اختر وجهتك:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "bac_schedule":
        schedule_files = bot_data.get("files", {}).get("exam_schedule_file", [])
        keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data="menu_bac")]]
        if schedule_files:
            await query.message.reply_document(document=schedule_files[0]["file_id"], caption="📅 برنامج الامتحانات الرسمية للفرع العلمي")
        else:
            await query.edit_message_text("📝 *برنامج الامتحان:*\n\n⚠️ لم يتم رفع برنامج الامتحان الرسمي بعد من قبل الإدارة.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "bac_subjects":
        keyboard = []
        sub_keys = list(SUBJECTS.keys())
        for i in range(0, len(sub_keys), 2):
            row = [
                InlineKeyboardButton(SUBJECTS[sub_keys[i]], callback_data=f"sub_{sub_keys[i]}"),
                InlineKeyboardButton(SUBJECTS[sub_keys[i+1]], callback_data=f"sub_{sub_keys[i+1]}") if i+1 < len(sub_keys) else None
            ]
            keyboard.append([b for b in row if b is not None])
        keyboard.append([InlineKeyboardButton("🔙 عودة للقسم السابق", callback_data="menu_bac")])
        await query.edit_message_text("📚 *اختر المادة الدراسية المراد تصفحها:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("sub_") and not data.startswith("subcat_"):
        subject_code = data.replace("sub_", "")
        subject_name = SUBJECTS[subject_code]
        
        keyboard = [
            [InlineKeyboardButton("📖 الكتاب المدرسي", callback_data=f"subcat_{subject_code}_book")],
            [InlineKeyboardButton("📝 الملخصات", callback_data=f"subcat_{subject_code}_notes")],
            [InlineKeyboardButton("📒 النوط", callback_data=f"subcat_{subject_code}_notebook")],
            [InlineKeyboardButton("💡 ملاحظات", callback_data=f"subcat_{subject_code}_remarks")],
        ]
        
        # إضافة خيارات الصوتيات الحصرية لمادة التربية الإسلامية فقط
        if subject_code == "islamic":
            keyboard.append([InlineKeyboardButton("🔊 الأحاديث بشكل صوتي", callback_data="audio_reciters_islamic_hadith_audio")])
            keyboard.append([InlineKeyboardButton("🔊 الآيات بشكل صوتي", callback_data="audio_reciters_islamic_quran_audio")])
            
        keyboard.append([InlineKeyboardButton("📂 أسئلة السنوات السابقة", callback_data=f"exmenu_{subject_code}")])
        keyboard.append([InlineKeyboardButton("🔙 تغيير المادة", callback_data="bac_subjects")] )
        await query.edit_message_text(f"📂 مادة *{subject_name}*\n\nاختر القسم المطلوب لتصفح ملفاته المحفوظة:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("exmenu_"):
        subject_code = data.replace("exmenu_", "")
        subject_name = SUBJECTS[subject_code]
        keyboard = [
            [InlineKeyboardButton("📅 حسب السنة", callback_data=f"subcat_{subject_code}_exams_year")],
            [InlineKeyboardButton("📝 كاملة", callback_data=f"subcat_{subject_code}_exams_all")],
            [InlineKeyboardButton("🔍 حسب البحث", callback_data=f"subcat_{subject_code}_exams_topic")],
            [InlineKeyboardButton("🔙 العودة للمادة", callback_data=f"sub_{subject_code}")]
        ]
        await query.edit_message_text(f"📂 أسئلة سنوات مادة *{subject_name}*\n\nاختر نوع التصنيف المراد عرضه:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # تصفح واختيار القراء لقسم الصوتيات بمادة الإسلامية
    elif data.startswith("audio_reciters_"):
        storage_key = data.replace("audio_reciters_", "")
        files_list = bot_data.get("files", {}).get(storage_key, [])
        subject_code = "islamic"
        keyboard = [[InlineKeyboardButton("🔙 عودة للمادة", callback_data=f"sub_{subject_code}")]]
        
        if not files_list:
            await query.edit_message_text("⚠️ لا يوجد ملفات صوتية مرفوعة في هذا القسم حالياً.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        # استخراج جميع القراء الفريدين
        reciters = set([f.get("reciter", "غير محدد") for f in files_list])
        reciter_keyboard = []
        for r in reciters:
            reciter_keyboard.append([InlineKeyboardButton(f"🎙️ القارئ: {r}", callback_data=f"viewaudio_{storage_key}_{r}")])
            
        reciter_keyboard.append([InlineKeyboardButton("🔙 عودة للمادة", callback_data=f"sub_{subject_code}")])
        await query.edit_message_text("🎙️ *قائمة القراء والمسموعات المتوفرة:*\n\nاختر اسم الشيخ أو القارئ للاستماع:", reply_markup=InlineKeyboardMarkup(reciter_keyboard), parse_mode="Markdown")

    # عرض الملفات الصوتية الخاصة بقارئ معين وإرسالها
    elif data.startswith("viewaudio_"):
        parts = data.split("_", 3)
        storage_key = f"{parts[1]}_{parts[2]}" # islamic_hadith/quran_audio
        reciter_name = parts[3]
        files_list = bot_data.get("files", {}).get(storage_key, [])
        
        keyboard = [[InlineKeyboardButton("🔙 عودة لقائمة القراء", callback_data=f"audio_reciters_{storage_key}")]]
        await query.message.reply_text(f"⏳ جاري جلب وإرسال التسجيلات الصوتية بصوت الشيخ/القارئ: {reciter_name}...")
        
        for f in files_list:
            if f.get("reciter") == reciter_name:
                if storage_key.endswith("audio"):
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f["file_id"], caption=f"🎵 {f['name']}")
                else:
                    await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=f"📄 {f['name']}")

    # إرسال الملفات العادية للأقسام الأخرى
    elif data.startswith("subcat_"):
        parts = data.split("_", 2)
        subject_code = parts[1]
        cat_type = parts[2]
        storage_key = f"{subject_code}_{cat_type}"
        files_list = bot_data.get("files", {}).get(storage_key, [])
        
        keyboard = [[InlineKeyboardButton("🔙 عودة للمادة", callback_data=f"sub_{subject_code}")]]
        if not files_list:
            await query.edit_message_text(f"⚠️ لا توجد ملفات مرفوعة حالياً في قسم: *{CATEGORIES[cat_type]}*.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
            
        await query.message.reply_text("⏳ جاري تحميل وإرسال الملفات المطلوبة...")
        for f in files_list:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=f"📄 {f['name']}")

    # --- إدارة تحكم الأدمن والرفع الشجري ---
    elif data.startswith("admin_set_subj_"):
        subject_code = data.replace("admin_set_subj_", "")
        context.user_data["upload_subj"] = subject_code
        
        if subject_code == "schedule":
            bot_data["files"]["exam_schedule_file"] = [{"name": context.user_data["last_file_name"], "file_id": context.user_data["last_file_id"]}]
            save_data(bot_data)
            await query.edit_message_text("✅ تم حفظ الملف وتحديثه كـ *برنامج الامتحان الرسمي* بنجاح!")
            context.user_data.clear()
            return

        # بناء أقسام الرفع للأدمن بناءً على نوع المادة
        keyboard = [
            [InlineKeyboardButton("📖 الكتاب المدرسي", callback_data="admin_set_cat_book")],
            [InlineKeyboardButton("📝 الملخصات", callback_data="admin_set_cat_notes")],
            [InlineKeyboardButton("📒 النوط", callback_data="admin_set_cat_notebook")],
            [InlineKeyboardButton("💡 ملاحظات", callback_data="admin_set_cat_remarks")]
        ]
        
        if subject_code == "islamic":
            keyboard.append([InlineKeyboardButton("🔊 الأحاديث بشكل صوتي", callback_data="admin_set_cat_hadith_audio")])
            keyboard.append([InlineKeyboardButton("🔊 الآيات بشكل صوتي", callback_data="admin_set_cat_quran_audio")])
            
        keyboard.extend([
            [InlineKeyboardButton("📅 أسئلة سنوات (حسب السنة)", callback_data="admin_set_cat_exams_year")],
            [InlineKeyboardButton("📝 أسئلة سنوات (كاملة)", callback_data="admin_set_cat_exams_all")],
            [InlineKeyboardButton("🔍 أسئلة سنوات (حسب البحث)", callback_data="admin_set_cat_exams_topic")]
        ])
        await query.edit_message_text(f"🎯 مادة: {SUBJECTS[subject_code]}\n\nاختر الآن قسم الفرز المطلوب للملف لحفظه فيه:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("admin_set_cat_"):
        cat_type = data.replace("admin_set_cat_", "")
        context.user_data["upload_cat"] = cat_type
        subject_code = context.user_data.get("upload_subj")
        
        # إذا كان المرفوع صوتيات مادة الإسلامية، نطلب اسم القارئ أولاً
        if subject_code == "islamic" and cat_type in ["hadith_audio", "quran_audio"]:
            await query.edit_message_text("🎙️ *قسم صوتيات التربية الإسلامية:*\n\nالرجاء إرسال اسم (القارئ أو الشيخ) نصياً الآن في المحادثة لربط الملف به:")
            context.user_data["waiting_for_reciter_name"] = True
            return
            
        # إتمام الحفظ للأقسام العادية مباشرة
        await complete_file_save(query.message, context)

async def complete_file_save(message, context, reciter_name=None):
    bot_data = load_data()
    subject_code = context.user_data.get("upload_subj")
    cat_type = context.user_data.get("upload_cat")
    file_id = context.user_data.get("last_file_id")
    file_name = context.user_data.get("last_file_name")
    
    storage_key = f"{subject_code}_{cat_type}"
    if "files" not in bot_data: bot_data["files"] = {}
    if storage_key not in bot_data["files"]: bot_data["files"][storage_key] = []
    
    file_entry = {"name": file_name, "file_id": file_id}
    if reciter_name:
        file_entry["reciter"] = reciter_name
        
    bot_data["files"][storage_key].append(file_entry)
    save_data(bot_data)
    
    msg_text = f"🚀 *تم الرفع والفرز التلقائي بنجاح!*\n\n📁 الملف: `{file_name}`\n📚 المادة: {SU
