import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# --- المتغيرات البيئية ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# 🔗 ضع هنا معرف حسابك الشخصي (التليجرام) لزر نشر الإعلان
YOUR_TELEGRAM_USERNAME = "Yousef55641" 

DATA_FILE = "bot_data.json"

# --- دالات إدارة البيانات ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "files": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"users": [], "files": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_user_if_new(user_id):
    data = load_data()
    if "users" not in data:
        data["users"] = []
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

# --- أسماء المواد والتصنيفات عربي / إنجليزي ---
SUBJECTS = {
    "math": "📐 الرياضيات",
    "phys": "⚡ الفيزياء",
    "chem": "🧪 الكيمياء",
    "science": "🧬 العلوم",
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
    "exams_topic": "🔍 أسئلة السنوات (حسب البحث)"
}

# --- القائمة الرئيسية للبوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user_if_new(update.effective_user.id)
    
    keyboard = [
        [InlineKeyboardButton("🎓 بكلوريا علمي", callback_data="menu_bac")],
        [InlineKeyboardButton("📢 نشر إعلان", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "👋 أهلاً بك في بوت سينا التعليمي مخصص لطلاب البكالوريا العلمية.\n\n"
        "الرجاء اختيار أحد الخيارات التالية من القائمة لتبدأ التصفح:",
        reply_markup=reply_markup
    )

# --- معالجة الضغط على الأزرار (التنقل والشجرة) ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    bot_data = load_data()

    # 1. قائمة بكلوريا علمي الرئيسية
    if data == "menu_bac":
        keyboard = [
            [InlineKeyboardButton("⏳ تبقى للامتحان", callback_data="bac_countdown")],
            [InlineKeyboardButton("📅 برنامج الامتحان", callback_data="bac_schedule")],
            [InlineKeyboardButton("📚 المواد الدراسية", callback_data="bac_subjects")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="menu_main")]
        ]
        await query.edit_message_text("🎓 *قسم البكالوريا العلمية*\n\nاختر ما تبحث عنه بدقة:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_main":
        keyboard = [
            [InlineKeyboardButton("🎓 بكلوريا علمي", callback_data="menu_bac")],
            [InlineKeyboardButton("📢 نشر إعلان", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
        ]
        await query.edit_message_text("👋 أهلاً بك مجدداً في بوت سينا التعليمي. اختر وجهتك:", reply_markup=InlineKeyboardMarkup(keyboard))

    # 2. عداد تنازلي للامتحان
    elif data == "bac_countdown":
        # حساب الوقت المتبقي (يمكنك تعديل التاريخ ليتناسب مع تاريخ الامتحان الفعلي)
        exam_date = datetime(2026, 6, 15) # مثال: 15 حزيران 2026
        remaining = exam_date - datetime.now()
        days = remaining.days
        
        text = f"⏳ *الوقت المتبقي للامتحانات الوزارية:*\n\n"
        if days > 0:
            text += f"باقي من الزمن تقريباً: *{days} يوم* شحذ الهمم يا بطل! 🔥"
        else:
            text += "🎯 الامتحانات بدأت بالفعل أو انتهت! بالتوفيق لجميع الطلاب."
            
        keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data="menu_bac")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 3. برنامج الامتحان
    elif data == "bac_schedule":
        # هنا يبحث البوت إذا كنت قد رفعت صورة أو ملف للبرنامج
        schedule_files = bot_data.get("files", {}).get("exam_schedule_file", [])
        keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data="menu_bac")]]
        
        if schedule_files:
            await query.message.reply_document(document=schedule_files[0]["file_id"], caption="📅 برنامج الامتحانات الرسمية للفرع العلمي")
        else:
            await query.edit_message_text("📝 *برنامج الامتحان:*\n\n⚠️ لم يتم رفع برنامج الامتحان الرسمي بعد من قِبل الإدارة.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 4. عرض المواد الدراسية
    elif data == "bac_subjects":
        keyboard = []
        # إنشاء أزرار للمواد صفين صفين
        sub_keys = list(SUBJECTS.keys())
        for i in range(0, len(sub_keys), 2):
            row = [
                InlineKeyboardButton(SUBJECTS[sub_keys[i]], callback_data=f"sub_{sub_keys[i]}"),
                InlineKeyboardButton(SUBJECTS[sub_keys[i+1]], callback_data=f"sub_{sub_keys[i+1]}") if i+1 < len(sub_keys) else None
            ]
            keyboard.append([b for b in row if b is not None])
            
        keyboard.append([InlineKeyboardButton("🔙 عودة للقسم السابق", callback_data="menu_bac")])
        await query.edit_message_text("📚 *اختر المادة الدراسية المراد تصفحها:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 5. عند اختيار مادة معينة (مثال: sub_phys)
    elif data.startswith("sub_") and not data.startswith("subcat_"):
        subject_code = data.replace("sub_", "")
        subject_name = SUBJECTS[subject_code]
        
        keyboard = [
            [InlineKeyboardButton("📖 الكتاب المدرسي", callback_data=f"subcat_{subject_code}_book")],
            [InlineKeyboardButton("📝 الملخصات", callback_data=f"subcat_{subject_code}_notes")],
            [InlineKeyboardButton("📒 النوط", callback_data=f"subcat_{subject_code}_notebook")],
            [InlineKeyboardButton("💡 ملاحظات", callback_data=f"subcat_{subject_code}_remarks")],
            [InlineKeyboardButton("📂 أسئلة السنوات السابقة", callback_data=f"exmenu_{subject_code}")],
            [InlineKeyboardButton("🔙 تغيير المادة", callback_data="bac_subjects")]
        ]
        await query.edit_message_text(f"📂 مادة *{subject_name}*\n\nاختر القسم المطلوب لتصفح ملفاته المحفوظة:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 6. قائمة أسئلة السنوات السابقة الفرعية داخل المادة
    elif data.startswith("exmenu_"):
        subject_code = data.replace("exmenu_", "")
        subject_name = SUBJECTS[subject_code]
        
        keyboard = [
            [InlineKeyboardButton("📅 حسب السنة", callback_data=f"subcat_{subject_code}_exams_year")],
            [InlineKeyboardButton("📝 كاملة", callback_data=f"subcat_{subject_code}_exams_all")],
            [InlineKeyboardButton("🔍 حسب البحث", callback_data=f"subcat_{subject_code}_exams_topic")],
            [InlineKeyboardButton("🔙 العودة للمادة", callback_data=f"sub__{subject_code}")] # عودة للمادة نفسها
        ]
        await query.edit_message_text(f"📂 أسئلة سنوات مادة *{subject_name}*\n\nاختر نوع التصنيف:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 7. إرسال الملفات للمستخدم بناءً على القسم والمادة المختارة
    elif data.startswith("subcat_"):
        parts = data.split("_", 2) # subcat, subject_code, cat_type
        subject_code = parts[1]
        cat_type = parts[2]
        
        storage_key = f"{subject_code}_{cat_type}"
        files_list = bot_data.get("files", {}).get(storage_key, [])
        
        keyboard = [[InlineKeyboardButton("🔙 عودة للمادة", callback_data=f"sub_{subject_code}")]]
        
        if not files_list:
            await query.edit_message_text(f"⚠️ لا يوجد ملفات مرفوعة حالياً في قسم: *{CATEGORIES[cat_type]}* لهذه المادة.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
            
        await query.message.reply_text(f"⏳ جاري تحميل وإرسال ملفات: {CATEGORIES[cat_type]}...")
        for f in files_list:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=f"📄 {f['name']}")


    # --- أقسام تحكم الأدمن لرفع وتوزيع الملفات تلقائياً ---
    elif data.startswith("admin_set_subj_"):
        subject_code = data.replace("admin_set_subj_", "")
        context.user_data["upload_subj"] = subject_code
        
        # إذا كانت المادة هي تحديد برنامج الامتحان، نحفظها مباشرة دون طلب تصنيف
        if subject_code == "schedule":
            bot_data = load_data()
            if "files" not in bot_data: bot_data["files"] = {}
            bot_data["files"]["exam_schedule_file"] = [{"name": context.user_data["last_file_name"], "file_id": context.user_data["last_file_id"]}]
            save_data(bot_data)
            await query.edit_message_text("✅ تم حفظ الملف بنجاح كـ *برنامج الامتحان الرسمي للبوت*!")
            return

        # عرض تصنيفات الملفات للأدمن
        keyboard = [
            [InlineKeyboardButton("📖 الكتاب المدرسي", callback_data="admin_set_cat_book")],
            [InlineKeyboardButton("📝 الملخصات", callback_data="admin_set_cat_notes")],
            [InlineKeyboardButton("📒 النوط", callback_data="admin_set_cat_notebook")],
            [InlineKeyboardButton("💡 ملاحظات", callback_data="admin_set_cat_remarks")],
            [InlineKeyboardButton("📂 أسئلة سنوات (حسب السنة)", callback_data="admin_set_cat_exams_year")],
            [InlineKeyboardButton("📝 أسئلة سنوات (كاملة)", callback_data="admin_set_cat_exams_all")],
            [InlineKeyboardButton("🔍 أسئلة سنوات (حسب البحث)", callback_data="admin_set_cat_exams_topic")]
        ]
        await query.edit_message_text(f"🎯 مادة: {SUBJECTS[subject_code]}\n\nاختر الآن نوع الملف المراد تصنيفه وحفظه:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("admin_set_cat_"):
        cat_type = data.replace("admin_set_cat_", "")
        subject_code = context.user_data.get("upload_subj")
        file_id = context.user_data.get("last_file_id")
        file_name = context.user_data.get("last_file_name")
        
        if not all([subject_code, file_id, file_name]):
            await query.edit_message_text("⚠️ حدث خطأ أو انتهت صلاحية الجلسة، يرجى إعادة إرسال الملف.")
            return
            
        storage_key = f"{subject_code}_{cat_type}"
        
        # حفظ الملف في قاعدة البيانات
        if "files" not in bot_data:
            bot_data["files"] = {}
        if storage_key not in bot_data["files"]:
            bot_data["files"][storage_key] = []
            
        bot_data["files"][storage_key].append({"name": file_name, "file_id": file_id})
        save_data(bot_data)
        
        await query.edit_message_text(
            text=f"🚀 *تم الحفظ بنجاح وتلقائياً!*\n\nالملف: `{file_name}`\nالمادة: {SUBJECTS[subject_code]}\nالقسم: {CATEGORIES[cat_type]}"
        )
        # تنظيف الذاكرة المؤقتة للامان
        context.user_data.clear()


# --- لوحة تحكم المسؤول (Admin Panel) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data = load_data()
    user_count = len(data.get("users", []))
    await update.message.reply_text(f"🔧 *مرحباً بك في لوحة تحكم بوت سينا*\n\n👥 عدد المشتركين: {user_count}\n\n💡 *طريقة إضافة الملفات للأقسام:*\nببساطة قم بإرسال أي ملف PDF هنا مباشرة في المحادثة وسيقوم البوت بسؤالك فوراً أين تود تصنيفه وحفظه.", parse_mode="Markdown")

# --- معالجة الملفات المرفوعة من الأدمن وتصنيفها شجرياً ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return

    file_id = update.message.document.file_id
    file_name = update.message.document.file_name

    context.user_data["last_file_id"] = file_id
    context.user_data["last_file_name"] = file_name

    # بناء أزرار اختيار المادة للأدمن
    keyboard = []
    sub_keys = list(SUBJECTS.keys())
    for i in range(0, len(sub_keys), 2):
        row = [
            InlineKeyboardButton(SUBJECTS[sub_keys[i]], callback_data=f"admin_set_subj_{sub_keys[i]}"),
            InlineKeyboardButton(SUBJECTS[sub_keys[i+1]], callback_data=f"admin_set_subj_{sub_keys[i+1]}") if i+1 < len(sub_keys) else None
        ]
        keyboard.append([b for b in row if b is not None])
        
    keyboard.append([InlineKeyboardButton("📅 رفعه كـ (برنامج الامتحان الرسمي)", callback_data="admin_set_subj_schedule")])
    
    await update.message.reply_text(
        text=f"📥 *تم استلام الملف بنجاح!* \nاسم الملف: `{file_name}`\n\nاختر المادة التابع لها هذا الملف:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- تشغيل البوت ---
def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Sina Bot updated tree structure running...")
    app.run_polling()

if __name__ == "__main__":
    main()
