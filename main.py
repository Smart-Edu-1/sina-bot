import os
import json
import random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "0"))
EXAM_DATE = date(2025, 6, 10)

SUBJECTS = {
    "math":    {"name": "📐 الرياضيات",         "book": None, "notes": None},
    "physics": {"name": "⚛️ الفيزياء",           "book": None, "notes": None},
    "chem":    {"name": "🧪 الكيمياء",           "book": None, "notes": None},
    "bio":     {"name": "🧬 الأحياء",            "book": None, "notes": None},
    "arabic":  {"name": "📖 اللغة العربية",      "book": None, "notes": None},
    "english": {"name": "🇬🇧 اللغة الإنجليزية", "book": None, "notes": None},
    "french":  {"name": "🇫🇷 اللغة الفرنسية",   "book": None, "notes": None},
    "phil":    {"name": "🧠 الفلسفة",            "book": None, "notes": None},
}

TIPS = [
    "💡 حلّ امتحانات السنوات السابقة أهم من حفظ الكتاب كاملاً!",
    "💡 راجع كل يوم 30 دقيقة أفضل من 5 ساعات قبل الامتحان.",
    "💡 اكتب الملخصات بيدك — ستحفظها ضعف السرعة.",
    "💡 نم 7-8 ساعات — النوم يثبّت المعلومات في الذاكرة.",
    "💡 قسّم المادة لأجزاء صغيرة وكافئ نفسك بعد كل جزء.",
    "💡 ابدأ بالمادة الأصعب وأنت نشيط، واترك الأسهل للآخر.",
    "💡 اشرح الدرس لنفسك بصوت عالٍ — إذا شرحته فهمته!",
    "💡 الفيزياء والرياضيات تحتاج تطبيق لا حفظ — حلّ مسائل يومياً.",
]

def save_user(user_id, name):
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = {}
    users[str(user_id)] = name
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False)

def get_users_count():
    try:
        with open("users.json", "r") as f:
            return len(json.load(f))
    except:
        return 0

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 الكتب المدرسية",     callback_data="books"),
         InlineKeyboardButton("📝 النوطات",            callback_data="notes")],
        [InlineKeyboardButton("📄 امتحانات سابقة",    callback_data="exams"),
         InlineKeyboardButton("⏱️ عداد الامتحان",     callback_data="countdown")],
        [InlineKeyboardButton("🔢 محول الوحدات",      callback_data="converter"),
         InlineKeyboardButton("📅 البرنامج الامتحاني",callback_data="schedule")],
        [InlineKeyboardButton("💡 نصيحة اليوم",       callback_data="tip"),
         InlineKeyboardButton("ℹ️ عن البوت",          callback_data="about")],
    ])

def subjects_keyboard(mode):
    rows = []
    items = list(SUBJECTS.items())
    for i in range(0, len(items), 2):
        row = []
        for key, val in items[i:i+2]:
            row.append(InlineKeyboardButton(val["name"], callback_data=f"{mode}_{key}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.first_name)
    text = f"""
🔬 *أهلاً {user.first_name} في بوت سينا!*

رفيقك العلمي لبكالوريا سوريا 🇸🇾
كل ما تحتاجه في مكان واحد ومجاناً ✨

📚 كتب مدرسية كاملة
📝 نوطات وملخصات
📄 امتحانات سابقة مع التصحيح
⏱️ عداد تنازلي للامتحان
🔢 محول الوحدات العلمية
📅 البرنامج الامتحاني

اختر من القائمة 👇
"""
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🔧 *لوحة تحكم بوت سينا*\n\n"
        f"👥 المستخدمون: *{get_users_count()}*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("📁 احصل على file_id", callback_data="admin_fileid")],
        ])
    )

def convert_units(value, from_u, to_u):
    table = {
        ("km","m"):1000,    ("m","km"):0.001,
        ("m","cm"):100,     ("cm","m"):0.01,
        ("cm","mm"):10,     ("mm","cm"):0.1,
        ("m","mm"):1000,    ("mm","m"):0.001,
        ("kg","g"):1000,    ("g","kg"):0.001,
        ("g","mg"):1000,    ("mg","g"):0.001,
        ("kg","mg"):1e6,    ("mg","kg"):1e-6,
        ("j","kj"):0.001,   ("kj","j"):1000,
        ("j","cal"):0.239,  ("cal","j"):4.184,
        ("kj","kcal"):0.239,("kcal","kj"):4.184,
        ("pa","atm"):9.869e-6,("atm","pa"):101325,
        ("bar","pa"):100000,  ("pa","bar"):1e-5,
        ("atm","bar"):1.01325,("bar","atm"):0.9869,
        ("m/s","km/h"):3.6,   ("km/h","m/s"):0.2778,
        ("l","ml"):1000,      ("ml","l"):0.001,
    }
    if from_u=="c" and to_u=="k": return value+273.15
    if from_u=="k" and to_u=="c": return value-273.15
    if from_u=="c" and to_u=="f": return value*9/5+32
    if from_u=="f" and to_u=="c": return (value-32)*5/9
    if from_u=="k" and to_u=="f": return (value-273.15)*9/5+32
    if from_u=="f" and to_u=="k": return (value-32)*5/9+273.15
    factor = table.get((from_u, to_u))
    return value*factor if factor else None

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.message.edit_text(
            "🔬 *بوت سينا* — اختر من القائمة 👇",
            parse_mode="Markdown", reply_markup=main_keyboard())

    elif data == "books":
        await query.message.edit_text(
            "📚 *الكتب المدرسية*\nاختر المادة:",
            parse_mode="Markdown", reply_markup=subjects_keyboard("book"))

    elif data.startswith("book_"):
        key = data.replace("book_","")
        sub = SUBJECTS.get(key)
        if sub and sub["book"]:
            await query.message.reply_document(sub["book"],
                caption=f"📚 {sub['name']} — بوت سينا 🔬")
        else:
            await query.message.reply_text(
                f"⏳ كتاب *{sub['name']}* سيُضاف قريباً! 🔔",
                parse_mode="Markdown")

    elif data == "notes":
        await query.message.edit_text(
            "📝 *النوطات والملخصات*\nاختر المادة:",
            parse_mode="Markdown", reply_markup=subjects_keyboard("notes"))

    elif data.startswith("notes_"):
        key = data.replace("notes_","")
        sub = SUBJECTS.get(key)
        if sub and sub["notes"]:
            await query.message.reply_document(sub["notes"],
                caption=f"📝 نوطة {sub['name']} — بوت سينا 🔬")
        else:
            await query.message.reply_text(
                f"⏳ نوطة *{sub['name']}* ستُضاف قريباً! 🔔",
                parse_mode="Markdown")

    elif data == "exams":
        await query.message.edit_text(
            "📄 *امتحانات سابقة*\nاختر المادة:",
            parse_mode="Markdown", reply_markup=subjects_keyboard("exam"))

    elif data.startswith("exam_"):
        await query.message.reply_text(
            "⏳ الامتحانات السابقة ستُضاف قريباً! 🔔")

    elif data == "countdown":
        today = date.today()
        delta = (EXAM_DATE - today).days
        if delta > 0:
            w, d = divmod(delta, 7)
            text = (f"⏱️ *عداد امتحان البكالوريا*\n\n"
                    f"تبقّى على الامتحان:\n"
                    f"🔴 *{delta} يوم* ({w} أسبوع و {d} أيام)\n\n"
                    f"📅 الموعد: {EXAM_DATE.strftime('%d/%m/%Y')}\n\n"
                    f"💪 كل يوم يعدّ — استغل وقتك!")
        elif delta == 0:
            text = "🚨 *الامتحان اليوم! بالتوفيق يا نجم* 🌟"
        else:
            text = "✅ *انتهى الامتحان! نتمنى لك التفوق* 🎓"
        await query.message.reply_text(text, parse_mode="Markdown")

    elif data == "converter":
        await query.message.reply_text("""
🔢 *محول الوحدات العلمية*

أرسل التحويل هكذا:
`القيمة الوحدة to الوحدة`

*أمثلة:*
`5 km to m`
`100 c to k`
`50 kg to g`
`2 atm to pa`
`72 km/h to m/s`

*الوحدات المدعومة:*
📏 km, m, cm, mm
⚖️ kg, g, mg
🌡️ c, k, f
⚡ j, kj, cal, kcal
🔵 pa, atm, bar
💨 m/s, km/h
🧪 l, ml
""", parse_mode="Markdown")

    elif data == "schedule":
        await query.message.reply_text("""
📅 *البرنامج الامتحاني — بكالوريا سوريا 2025*
*(الفرع العلمي)*

1️⃣ اللغة العربية
2️⃣ الرياضيات
3️⃣ الفيزياء
4️⃣ الكيمياء
5️⃣ الأحياء
6️⃣ اللغة الإنجليزية
7️⃣ الفلسفة والاجتماع

⏰ التوقيت: 8:00 صباحاً
_سيُحدَّث بالتواريخ الرسمية فور إعلانها_ 📢
""", parse_mode="Markdown")

    elif data == "tip":
        await query.message.reply_text(random.choice(TIPS))

    elif data == "about":
        await query.message.reply_text("""
🔬 *بوت سينا*
_رفيقك العلمي لبكالوريا سوريا_ 🇸🇾

مستوحى من *ابن سينا* — عالم العرب الأعظم 🌟

للتواصل والاقتراحات تواصل مع المشرف
""", parse_mode="Markdown")

    elif data == "admin_stats":
        await query.message.reply_text(
            f"📊 *إحصائيات بوت سينا*\n\n👥 المستخدمون: *{get_users_count()}*",
            parse_mode="Markdown")

    elif data == "admin_fileid":
        await query.message.reply_text(
            "📁 أرسل أي ملف PDF وسأعطيك الـ file\\_id",
            parse_mode="Markdown")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    parts = text.split()
    if len(parts) == 4 and parts[2] == "to":
        try:
            value = float(parts[0])
            result = convert_units(value, parts[1], parts[3])
            if result is not None:
                await update.message.reply_text(
                    f"✅ `{value} {parts[1]}` = *{result:.4f} {parts[3]}*",
                    parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ تحويل غير مدعوم.\nمثال: `5 km to m`", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ صيغة خاطئة.\nمثال: `5 km to m`", parse_mode="Markdown")
        return
    await update.message.reply_text("اضغط /start للقائمة 🔬")

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.message.document:
        fid = update.message.document.file_id
        name = update.message.document.file_name
        await update.message.reply_text(
            f"📎 *{name}*\n\n`{fid}`", parse_mode="Markdown")
    elif update.message.photo:
        fid = update.message.photo[-1].file_id
        await update.message.reply_text(f"🖼️\n`{fid}`", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    app.add_handler(MessageHandler(filters.PHOTO, file_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("🔬 بوت سينا يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
