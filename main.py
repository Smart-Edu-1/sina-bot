    import os
import json
import random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# جلب المتغيرات البيئية من Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

DATA_FILE = "bot_data.json"

# --- دالات إدارة قاعدة البيانات المؤقتة (JSON) ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"books": [], "notes": [], "exams": [], "users": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"books": [], "notes": [], "exams": [], "users": []}

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

# --- الأوامر العامة للمستخدمين ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user_if_new(user_id)
    
    await update.message.reply_text(
        "👋 أهلاً بك في بوت سينا التعليمي مخصص لطلاب البكالوريا العلمية!\n\n"
        "استخدم القائمة أو الأوامر التالية لتصفح الملفات:\n"
        "📚 /books - قسم الكتب المدرسيّة\n"
        "📝 /notes - قسم الملخصات والمكثفات\n"
        "📋 /exams - قسم النماذج والامتحانات"
    )

async def send_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user_if_new(update.effective_user.id)
    data = load_data()
    files = data.get("books", [])
    
    if not files:
        await update.effective_message.reply_text("⚠️ هذا القسم فارغ حالياً، سيقوم الأدمن بإضافة الملفات قريباً!")
        return
        
    await update.effective_message.reply_text("⏳ جاري إرسال الكتب والمصادر المتاحة...")
    for f in files:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=f"📘 {f['name']}")

async def send_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user_if_new(update.effective_user.id)
    data = load_data()
    files = data.get("notes", [])
    
    if not files:
        await update.effective_message.reply_text("⚠️ هذا القسم فارغ حالياً، سيقوم الأدمن بإضافة الملفات قريباً!")
        return
        
    await update.effective_message.reply_text("⏳ جاري إرسال الملخصات والمكثفات...")
    for f in files:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=f"📝 {f['name']}")

async def send_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user_if_new(update.effective_user.id)
    data = load_data()
    files = data.get("exams", [])
    
    if not files:
        await update.effective_message.reply_text("⚠️ هذا القسم فارغ حالياً، سيقوم الأدمن بإضافة النماذج قريباً!")
        return
        
    await update.effective_message.reply_text("⏳ جاري إرسال النماذج والامتحانات الوزارية...")
    for f in files:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f["file_id"], caption=f"📋 {f['name']}")


# --- لوحة تحكم المسؤول (Admin Panel) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    data = load_data()
    user_count = len(data.get("users", []))

    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("📂 احصل على file_id", callback_data="admin_get_id")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=f"🔧 *لوحة تحكم بوت سينا*\n\n👥 المستخدمون: {user_count}",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


# --- معالجة الملفات المرفوعة من الأدمن ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    file_id = update.message.document.file_id
    file_name = update.message.document.file_name

    # حفظ بيانات الملف مؤقتاً في جلسة الأدمن لتفادي مشكلة الـ 64 بت في الأزرار
    context.user_data["last_file_id"] = file_id
    context.user_data["last_file_name"] = file_name

    keyboard = [
        [
            InlineKeyboardButton("📚 قسم الكتب", callback_data="save_books"),
            InlineKeyboardButton("📝 قسم الملخصات", callback_data="save_notes")
        ],
        [
            InlineKeyboardButton("📋 قسم الامتحانات", callback_data="save_exams")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # إرسال الـ ID وعرض الأزرار لتحديد القسم فوراً
    await update.message.reply_text(
        text=f"📂 *مواضيع وملفات بوت سينا*\n\n`{file_id}`\n\nاختر القسم الذي تريد حفظ الملف فيه مباشرة:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


# --- معالجة الضغط على الأزرار الشفافة (Callback Queries) ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    bot_data = load_data()

    if data == "admin_stats":
        user_count = len(bot_data.get("users", []))
        await query.message.reply_text(f"📊 *إحصائيات بوت سينا*\n\n👥 المستخدمون: {user_count}", parse_mode="Markdown")
        
    elif data == "admin_get_id":
        await query.message.reply_text("📂 أرسل أي ملف PDF وسأعطيك الـ `file_id` وخيارات الحفظ التلقائي.", parse_mode="Markdown")
        
    elif data in ["save_books", "save_notes", "save_exams"]:
        file_id = context.user_data.get("last_file_id")
        file_name = context.user_data.get("last_file_name")

        if not file_id or not file_name:
            await query.edit_message_text("⚠️ عذراً، انتهت صلاحية الجلسة المفتوحة للملف. يرجى إعادة إرسال الملف مرة أخرى.")
            return

        category = data.replace("save_", "")
        
        # إضافة الملف للقسم المناسب
        bot_data[category].append({"name": file_name, "file_id": file_id})
        save_data(bot_data)

        categories_titles = {"books": "الكتب 📚", "notes": "الملخصات 📝", "exams": "الامتحانات 📋"}
        
        await query.edit_message_text(
            text=f"🚀 تم بنجاح إضافة ملف: *{file_name}*\nإلى قسم: *{categories_titles[category]}* الحفظ تم تلقائياً!"
        )
        
        # تنظيف الذاكرة المؤقتة بعد الحفظ
        context.user_data.pop("last_file_id", None)
        context.user_data.pop("last_file_name", None)


# --- تشغيل البوت الأساسي ---
def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not found.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # ربط الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("books", send_books))
    app.add_handler(CommandHandler("notes", send_notes))
    app.add_handler(CommandHandler("exams", send_exams))
    app.add_handler(CommandHandler("admin", admin_panel))

    # ربط معالجة الملفات والضغط على الأزرار
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Sina Bot is running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
