import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from supabase import create_client, Client

# --- المتغيرات البيئية وبيانات الربط ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
YOUR_TELEGRAM_USERNAME = "Yousef55641" # يوزرك الخاص للتعرف عليك كمسؤول

SUPABASE_URL = "https://syrpxdwypyisvlmwmmbu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN5cnB4ZHd5cHlpc3ZsbXdtbWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MjE2MDEsImV4cCI6MjA5NjQ5NzYwMX0.kG2PzNGb3ta9vu58gZrkCYZJ0YTk3VhsNTa-6fiUZ3M"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SUBJECTS = {
    "📐 الرياضيات": "math",
    "⚡ الفيزياء": "phys",
    "🧪 الكيمياء": "chem",
    "🧬 العلوم": "science",
    "🕋 التربية الإسلامية": "islamic",
    "📚 اللغة العربية": "arabic",
    "🇬🇧 اللغة الإنجليزية": "english",
    "🇫🇷 اللغة الفرنسية": "french",
}

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
        print(f"Error registering student: {e}")

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📚 تصفح المواد الدراسية"), KeyboardButton("البكلوريا العلمي 🔬")],
        [KeyboardButton("📢 طلب إعلان للمكتبة"), KeyboardButton("💬 تواصل مع الإدارة")]
    ], resize_keyboard=True, input_field_placeholder="اختر من القائمة الرئيسية...")

def get_subjects_keyboard():
    return ReplyKeyboardMarkup([
        ["⚡ الفيزياء", "📐 الرياضيات"],
        ["🧬 العلوم", "🧪 الكيمياء"],
        ["📚 اللغة العربية", "🕋 التربية الإسلامية"],
        ["🇫🇷 اللغة الفرنسية", "🇬🇧 اللغة الإنجليزية"],
        ["🔙 العودة للقائمة الرئيسية"]
    ], resize_keyboard=True, input_field_placeholder="اختر المادة لتصفح رصيد ملفاتها...")

def get_categories_keyboard(subject_name):
    keyboard = [
        ["📝 الملخصات الذهنية", "📖 الكتاب المدرسي"],
        ["💡 ملاحظات تذكيرية", "📒 النوط الشاملة"],
        ["📂 أسئلة السنوات السابقة"]
    ]
    if "الإسلامية" in subject_name or "🕋" in subject_name:
        keyboard.insert(2, ["🔊 الأحاديث الشريفة", "🔊 الآيات القرآنية"])
    keyboard.append(["🔙 تغيير المادة المحددة"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="اختر القسم المطلوب...")

def get_exams_keyboard():
    return ReplyKeyboardMarkup([
        ["📅 حسب السنة", "📝 كاملة الشرح"],
        ["🔍 حسب الأبحاث"],
        ["🔙 العودة لأقسام المادة"]
    ], resize_keyboard=True, input_field_placeholder="اختر طريقة فرز الأسئلة...")

async def catch_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        f_id = update.message.document.file_id
        await update.message.reply_text(f"📄 تم التقاط معرف المستند بنجاح!\n\n{f_id}")
    elif update.message.audio:
        f_id = update.message.audio.file_id
        await update.message.reply_text(f"🔊 تم التقاط معرف الملف الصوتي بنجاح!\n\n{f_id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await register_student_to_supabase(update.effective_user)
    context.user_data.clear() 
    await update.effective_message.reply_text(
        "👋 أهلاً بك في بوت المكتبة التعليمية لطلاب البكالوريا العلمية.\n\nيرجى استخدام القائمة السفلية للتصفح السلس والمنظم:",
        reply_markup=get_main_keyboard()
    )

async def handle_bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data
    is_admin = (update.effective_user.username == YOUR_TELEGRAM_USERNAME)

    if "العودة للقائمة الرئيسية" in text or text == "🏠 الرئيسية":
        user_data.clear()
        await update.message.reply_text("🔙 تم العودة للقائمة الرئيسية للخدمات:", reply_markup=get_main_keyboard())
        return

    elif "البكلوريا العلمي" in text or "تصفح المواد" in text or "تغيير المادة" in text:
        await update.message.reply_text("📚 اختر المادة التي ترغب بتصفح ملفاتها بالأيقونات الرسومية المحدثة الأنيقة:", reply_markup=get_subjects_keyboard())
        return

    elif "طلب إعلان" in text or "تواصل مع الإدارة" in text:
        await update.message.reply_text(f"💬 يمكنك التواصل مباشرة مع إدارة المكتبة والموقع عبر الحساب الرسمي التالي:\n\n🔗 @{YOUR_TELEGRAM_USERNAME}")
        return

    # فحص المادة المحددة
    matched_subject = None
    for k in SUBJECTS.keys():
        pure_subject_name = k.replace("📐","").replace("⚡","").replace("🧪","").replace("🧬","").replace("🕋","").replace("📚","").replace("🇬🇧","").replace("🇫🇷","").strip()
        if pure_subject_name in text:
            matched_subject = k
            break

    if matched_subject:
        user_data["current_subject_name"] = matched_subject
        user_data["current_subject_code"] = SUBJECTS[matched_subject]
        await update.message.reply_text(f"✨ لقد فتحت الآن رفوف مادة:\n🎯 {matched_subject}\n\nيرجى تحديد التصنيف المراد عرضه من الأزرار بالأسفل:", reply_markup=get_categories_keyboard(matched_subject))
        return

    if "أسئلة السنوات السابقة" in text or "📂 أسئلة السنوات" in text:
        if "current_subject_code" not in user_data:
            await update.message.reply_text("⚠️ يرجى اختيار المادة أولاً.", reply_markup=get_subjects_keyboard())
            return
        await update.message.reply_text("📅 اختر طريقة عرض الفرز لأسئلة السنوات السابقة:", reply_markup=get_exams_keyboard())
        return

    if "العودة لأقسام المادة" in text:
        if "current_subject_name" not in user_data:
            await update.message.reply_text("⚠️ انتهت الجلسة، يرجى إعادة اختيار المادة:", reply_markup=get_subjects_keyboard())
            return
        subject_name = user_data["current_subject_name"]
        await update.message.reply_text(f"📂 تم العودة لقائمة أقسام مادة:\n🎯 {subject_name}", reply_markup=get_categories_keyboard(subject_name))
        return

    # خريطة التصنيفات الافتراضية
    cat_map = {
        "حسب السنة": "exams_year",
        "كاملة الشرح": "exams_all",
        "حسب الأبحاث": "exams_topic",
        "الملخصات": "notes",
        "الكتاب المدرسي": "textbook",  
        "النوط الشاملة": "notebook",
        "ملاحظات تذكيرية": "remarks",
        "الأحاديث": "hadith_audio",
        "الآيات": "quran_audio"
    }
    
    matched_category_code = None
    for k, v in cat_map.items():
        if k in text:
            matched_category_code = v
            break

    if matched_category_code:
        if "current_subject_code" not in user_data:
            await update.message.reply_text("⚠️ انتهت الجلسة، يرجى إعادة اختيار المادة:", reply_markup=get_subjects_keyboard())
            return
        
        subject_code = user_data["current_subject_code"]
        subject_name = user_data["current_subject_name"]
        loading_msg = await update.message.reply_text("⏳ جاري فحص المستندات في قاعدة البيانات...")
        
        files_list = []
        try:
            # محاولة البحث بالفلاتر المعتمدة
            res1 = await asyncio.to_thread(
                lambda: supabase.table("materials").select("*").eq("subject", subject_code).eq("category", matched_category_code).execute()
            )
            if res1.data:
                files_list = res1.data
            
            if not files_list:
                res2 = await asyncio.to_thread(
                    lambda: supabase.table("materials").select("*").eq("subject", subject_name).eq("category", text).execute()
                )
                if res2.data:
                    files_list = res2.data
            
            if not files_list:
                pure_sub = subject_name.replace("📐","").replace("⚡","").replace("🧪","").replace("🧬","").replace("🕋","").replace("📚","").replace("🇬🇧","").replace("🇫🇷","").strip()
                pure_cat = text.replace("📝","").replace("📖","").replace("💡","").replace("📒","").replace("📂","").strip()
                res3 = await asyncio.to_thread(
                    lambda: supabase.table("materials").select("*").eq("subject", pure_sub).eq("category", pure_cat).execute()
                )
                if res3.data:
                    files_list = res3.data

        except Exception as e:
            # معالجة الخطأ: الطالب يرى رسالة عامة، والمسؤول يرى التفاصيل التقنية
            if is_admin:
                await loading_msg.edit_text(f"⚠️ خطأ اتصال بالسيرفر (يظهر لك بصفتك المطور تنبيه فقط):\n\n{str(e)}")
            else:
                await loading_msg.edit_text("⚠️ عذراً، واجهنا مشكلة مؤقتة في جلب الملفات، يرجى المحاولة مرة أخرى لاحقاً.")
            return
        
        # عند عدم العثور على أي ملفات
        if not files_list:
            if is_admin:
                # رادار التشخيص الذكي يظهر لك أنت فقط للتعرف على الأسماء الحقيقية للمواد والتصنيفات
                try:
                    debug_res = await asyncio.to_thread(
                        lambda: supabase.table("materials").select("*").limit(5).execute()
                    )
                    if debug_res.data:
                        debug_msg = "🔍 لوحة تشخيص المطور الذكية (تظهر لك أنت فقط):\n\n"
                        debug_msg += "القسم الحالي فارغ. إليك عينة من الحقول المخزنة بجدولك لرؤية الكلمات الحقيقية:\n\n"
                        for idx, row in enumerate(debug_res.data, 1):
                            debug_msg += f"📋 ملف رقم {idx}:\n"
                            debug_msg += f"🔹 الاسم الحركي: {row.get('file_name') or row.get('title') or row.get('name')}\n"
                            debug_msg += f"🔹 عمود المادة (subject): `{row.get('subject')}`\n"
                            debug_msg += f"🔹 عمود القسم (category): `{row.get('category')}`\n"
                            debug_msg += "--------------------\n"
                        debug_msg += "\n💡 قم بنسخ الكلمة المكتوبة أمام (category) للملف الذي وضعته في الملخصات وأرسلها لي لأقوم بربطها!"
                        await loading_msg.edit_text(debug_msg)
                        return
                except Exception:
                    pass
            
            # الرسالة الرسمية الأنيقة التي تظهر للطالب دائماً
            await loading_msg.edit_text(f"⚠️ لا توجد ملفات مرفوعة حالياً في قسم ({text}) لمادة {subject_name}.")
            return

        try:
            await loading_msg.delete()
        except Exception:
            pass
        
        # إرسال الملفات المكتشفة للمستخدمين
        for f in files_list:
            try:
                file_name = f.get("file_name") or f.get("title") or f.get("name") or "ملف تعليمي"
                caption_text = f"📄 {file_name}"
                
                f_id = f.get("file_id") or f.get("telegram_file_id")
                f_url = f.get("file_url") or f.get("url") or f.get("file_path") or f.get("pdf_url")
                
                if f_id:
                    if matched_category_code in ["hadith_audio", "quran_audio"]:
                        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f_id, caption=caption_text)
                    else:
                        await context.bot.send_document(chat_id=update.effective_chat.id, document=f_id, caption=caption_text)
                elif f_url:
                    try:
                        if matched_category_code in ["hadith_audio", "quran_audio"]:
                            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f_url, caption=caption_text)
                        else:
                            await context.bot.send_document(chat_id=update.effective_chat.id, document=f_url, caption=caption_text)
                    except Exception:
                        await update.message.reply_text(f"{caption_text}\n\n🔗 رابط التحميل المباشر:\n{f_url}")
                else:
                    if is_admin:
                        await update.message.reply_text(f"⚠️ الأعمدة فارغة للمطور. الحقول المتاحة بالجدول: {', '.join(list(f.keys()))}")
            except Exception:
                continue
        return

    await update.message.reply_text("ℹ️ من فضلك، استخدم أزرار القائمة السفلية الظاهرة أمامك للتنقل.", reply_markup=get_main_keyboard())

async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO, catch_file_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
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
                
