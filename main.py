import os
import json
import asyncio
from datetime import datetime
from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# --- المتغيرات البيئية ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
YOUR_TELEGRAM_USERNAME = "Yousef55641" 

# جلب رابط الاستضافة التلقائي من Railway لتشغيل نافذة العداد التنازلي المدمجة
PUBLIC_URL = os.environ.get("RAILWAY_STATIC_URL", "")
if PUBLIC_URL and not PUBLIC_URL.startswith("https://"):
    PUBLIC_URL = f"https://{PUBLIC_URL}"

DATA_FILE = "bot_data.json"

# --- دالات إدارة وحفظ البيانات ---
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

# --- المصفوفات الثابتة للمواد والتصنيفات ---
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

# --- صفحة العداد التنازلي الاحترافية (HTML/CSS) للنافذة المنبثقة WebApp ---
async def countdown_page(request):
    data = load_data()
    exam_date_str = data.get("exam_date", "2026-06-15")
    
    # نص عادي تماماً بدون f-string لمنع حدوث مشاكل فك الأقواس مع جافا سكريبت نهائياً
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

# --- عرض القائمة الرئيسية (تصميم أزرار شبكية مريحة) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user_if_new(update.effective_user.id)
    
    keyboard = [
        [KeyboardButton("📢 نشر إعلان"), KeyboardButton("🎓 بكلوريا علمي")],
        [KeyboardButton("🏠 الرئيسية")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, placeholder="اختر القسم المطلوب من هنا...")
    
    await update.effective_message.reply_text(
        "👋 أهلاً بك في بوت سينا التعليمي المخصص لطلاب البكالوريا العلمية.\n\n"
        "الرجاء اختيار أحد الأقسام من الأزرار المتاحة أسفل الشاشة لبدء التصفح الفرعي والمنظم للدروس والملفات:",
        reply_markup=reply_markup
    )

# --- معالجة الأزرار النصية (الأسفل) وزر الرئيسية ---
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    
    if user_text == "🏠 الرئيسية":
        await start(update, context)
        return

    elif user_text == "🎓 بكلوريا علمي":
        webapp_url = f"{PUBLIC_URL}/countdown" if PUBLIC_URL else "https://google.com"
        keyboard = [
            [InlineKeyboardButton("⏳ تبقى للامتحان (اضغط لفتح النافذة)", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton("📅 برنامج الامتحان", callback_data="bac_schedule")],
            [InlineKeyboardButton("📚 المواد الدراسية", callback_data="bac_subjects")]
        ]
        await update.message.reply_text(
            "🎓 *العام الدراسي 2026 - بكالوريا علمي*\n\nاختر من القائمة الذكية ما تبحث عنه لتصفحه فوراُ:", 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown"
        )
        return

    elif user_text == "📢 نشر إعلان":
        keyboard = [[InlineKeyboardButton("💬 تواصل معي لنشر إعلانك الآن", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]]
        await update.message.reply_text(
            "📢 يمكنك نشر إعلاناتك بسهولة عبر البوت.\n\nاضغط على الزر أدناه ليتم تحويلك مباشرة لملفي الشخصي لإرسال التفاصيل:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # استقبال تواصل الأدمن ونصوص التعديل
    if update.effective_user.id == ADMIN_ID:
        if context.user_data.get("waiting_for_reciter_name"):
            reciter_name = user_text
            await complete_file_save(update.message, context, reciter_name=reciter_name)
            return

        if user_text.startswith("/setdate "):
            new_date = user_text.replace("/setdate ", "").strip()
            try:
                datetime.strptime(new_date, "%Y-%m-%d")
                data = load_data()
                data["exam_date"] = new_date
                save_data(data)
                await update.message.reply_text(f"✅ تم تحديث تاريخ الامتحان للعداد بنجاح إلى: `{new_date}`", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("⚠️ صيغة التاريخ خاطئة! يرجى إرسالها هكذا: `2026-06-15`")

# --- معالجة الضغط على أزرار لوحة التصفح الداخلية الشجرية ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    bot_data = load_data()

    if data == "bac_subjects":
        keyboard = []
        sub_keys = list(SUBJECTS.keys())
        for i in range(0, len(sub_keys), 2):
            row = [
                InlineKeyboardButton(SUBJECTS[sub_keys[i]], callback_data=f"sub_{sub_keys[i]}"),
                InlineKeyboardButton(SUBJECTS[sub_keys[i+1]], callback_data=f"sub_{sub_keys[i+1]}") if i+1 < len(sub_keys) else None
            ]
            keyboard.append([b for b in row if b is not None])
        await query.edit_message_text("📚 *اختر المادة الدراسية المراد تصفح أقسامها ومحتوياتها:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("sub_") and not data.startswith("subcat_"):
        subject_code = data.replace("sub_", "")
        subject_name = SUBJECTS[subject_code]
        
        keyboard = [
            [InlineKeyboardButton("📖 الكتاب المدرسي", callback_data=f"subcat_{subject_code}_book")],
            [InlineKeyboardButton("📝 الملخصات", callback_data=f"subcat_{subject_code}_notes")],
            [InlineKeyboardButton("📒 النوط", callback_data=f"subcat_{subject_code}_notebook")],
            [InlineKeyboardButton("💡 ملاحظات", callback_data=f"subcat_{subject_code}_remarks")],
        ]
        
        if subject_code == "islamic":
            keyboard.append([InlineKeyboardButton("🔊 الأحاديث بشكل صوتي", callback_data="audio_reciters_islamic_hadith_audio")])
            keyboard.append([InlineKeyboardButton("🔊 الآيات بشكل صوتي", callback_data="audio_reciters_islamic_quran_audio")])
            
        keyboard.append([InlineKeyboardButton("📂 أسئلة السنوات السابقة", callback_data=f"exmenu_{subject_code}")])
        keyboard.append([InlineKeyboardButton("🔙 العودة للمواد", callback_data="bac_subjects")])
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
        await query.edit_message_text(f"📂 أسئلة سنوات مادة *{subject_name}*\n\nاختر نوع تصنيف الفرز المطلوب:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("audio_reciters_"):
        storage_key = data.replace("audio_reciters_", "")
        files_list = bot_data.get("files", {}).get(storage_key, [])
        keyboard = [[InlineKeyboardButton("🔙 عودة للمادة", callback_data="sub_islamic")]]
        
        if not files_list:
            await query.edit_message_text("⚠️ لا توجد ملفات صوتية مرفوعة في هذا القسم حالياً.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        reciters = set([f.get("reciter", "غير محدد") for f in files_list])
        reciter_keyboard = []
        for r in reciters:
            reciter_keyboard.append([InlineKeyboardButton(f"🎙️ القارئ: {r}", callback_data=f"viewaudio_{storage_key}_{r}")])
        reciter_keyboard.append([InlineKeyboardButton("🔙 عودة لمادة الإسلامية", callback_data="sub_islamic")])
        await query.edit_message_text("🎙️ *قائمة القراء والمسموعات المتوفرة للقسم:*", reply_markup=InlineKeyboardMarkup(reciter_keyboard), parse_mode="Markdown")

    elif data.startswith("viewaudio_"):
        parts = data.split("_", 3)
        storage_key = f"{parts[1]}_{parts[2]}"
        reciter_name = parts[3]
        files_list = bot_data.get("files", {}).get(storage_key, [])
        
        await query.message.reply_text(f"⏳ جاري جلب وإرسال التسجيلات الصوتية بصوت القارئ: {reciter_name}...")
        for f in files_list:
            if f.get("reciter") == reciter_name:
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f["file_id"], caption=f"🎵 {f['name']}")

    elif data.startswith("subcat_"):
        parts = data.split("_", 2)
        subject_code = parts[1]
        cat_type = parts[2]
        storage_key = f"{subject_code}_{cat_type}"
        files_list = bot_data.get("files", {}).get(storage_key, [])
        
        keyboard = [[InlineKeyboardButton("🔙 عودة للمادة", callback_data=f"sub_{subject_code}")]]
        if not files_list:
            cat_name = CATEGORIES.get(cat_type, cat_type)
            await query.edit_message_text(f"⚠️ لا توجد ملفات مرفوعة حالياً في قسم: *{cat_name}*.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
            
        await query.message.reply_text("⏳ جاري تحميل وإرسال الملفات المطلوبة للقسم المختار...")
        for f in files_list:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=f"📄 {f['name']}")

    elif data == "bac_schedule":
        schedule_files = bot_data.get("files", {}).get("exam_schedule_file", [])
        if schedule_files:
            await query.message.reply_document(document=schedule_files[0]["file_id"], caption="📅 برنامج الامتحانات الوزارية للفرع العلمي المعتمد")
        else:
            await query.message.reply_text("📝 برنامج الامتحان الرسمي لم يتم رفعه وتثبيته بعد من قبل الإدارة.")

    # خطوات رفع وتصنيف الملفات للأدمن
    elif data.startswith("admin_set_subj_"):
        subject_code = data.replace("admin_set_subj_", "")
        context.user_data["upload_subj"] = subject_code
        
        if subject_code == "schedule":
            bot_data["files"]["exam_schedule_file"] = [{"name": context.user_data["last_file_name"], "file_id": context.user_data["last_file_id"]}]
            save_data(bot_data)
            await query.edit_message_text("✅ تم حفظ وتثبيت الملف كـ *برنامج الامتحان الرسمي للبوت*!")
            context.user_data.clear()
            return

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
        await query.edit_message_text(f"🎯 مادة: {SUBJECTS[subject_code]}\n\nاختر نوع فرز وحفظ هذا الملف المرفوع بداخلها:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("admin_set_cat_"):
        cat_type = data.replace("admin_set_cat_", "")
        context.user_data["upload_cat"] = cat_type
        subject_code = context.user_data.get("upload_subj")
        
        if subject_code == "islamic" and cat_type in ["hadith_audio", "quran_audio"]:
            await query.edit_message_text("🎙️ *محتوى صوتي إسلامي:*\n\nالرجاء كتابة اسم (القارئ أو الشيخ) نصياً الآن في الشات لإتمام عملية الربط والعرض:")
            context.user_data["waiting_for_reciter_name"] = True
            return
            
        await complete_file_save(query.message, context)

# --- إتمام الحفظ النهائي وتفادي أخطاء الـ SyntaxError القديمة ---
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
    
    subj_title = SUBJECTS.get(subject_code, subject_code)
    cat_title = CATEGORIES.get(cat_type, cat_type)
    
    msg_text = f"🚀 *تم الفرز التلقائي وحفظ الملف بنجاح!*\n\n📁 الملف: `{file_name}`\n📚 المادة: {subj_title}\n📂 التصنيف: {cat_title}"
    if reciter_name:
        msg_text += f"\n🎙️ بصوت الشيخ/القارئ: {reciter_name}"
        
    await message.reply_text(msg_text, parse_mode="Markdown")
    context.user_data.clear()

# --- معالجة استقبال الملفات والصوتيات المرفوعة من الأدمن ---
async def handle_document_or_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return

    file_id = None
    file_name = "ملف_غير_معروف"

    # التحقق إذا كان المرفق ملفاً عاديًا (PDF، نوطة، إلخ)
    if update.message.document:
        fi
