import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from supabase import create_client, Client

# --- المتغيرات البيئية وبيانات الربط ---
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
        [KeyboardButton("البكلوريا العلمي 🎓")],
        [KeyboardButton("📢 طلب إعلان للمكتبة"), KeyboardButton("💬 تواصل مع الإدارة")]
    ], resize_keyboard=True, input_field_placeholder="اختر من القائمة الرئيسية...")

def get_subjects_keyboard():
    return ReplyKeyboardMarkup([
        ["🧲 الفيزياء", "📐 الرياضيات"],
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

# 🌟 تعديل الخيار الأول ليكون "📝 كاملة" بناءً على طلبك
def get_exams_keyboard():
    return ReplyKeyboardMarkup([
        ["📅 حسب السنة", "📝 كاملة"],
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

async def debug_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != YOUR_TELEGRAM_USERNAME:
        await update.message.reply_text("⚠️ هذا الأمر مخصص لإدارة المنصة فقط.")
        return
    
    loading = await update.message.reply_text("⏳ جاري قراءة محتويات جدول المواد الحالية...")
    try:
        res = await asyncio.to_thread(
            lambda: supabase.table("materials").select("*").limit(10).execute()
        )
        if not res.data:
            await loading.edit_text("📂 الجدول فارغ تماماً حالياً في قاعدة البيانات.")
            return
        
        msg = "📋 قائمة الملفات المتوفرة والأسماء السرية المخزنة حالياً:\n\n"
        for idx, row in enumerate(res.data, 1):
            name = row.get('file_name') or row.get('title') or row.get('name') or 'بدون اسم'
            msg += f"{idx}- الملف: {name}\n"
            msg += f"🔹 المادة (subject): {row.get('subject')}\n"
            msg += f"🔹 القسم (category): {row.get('category')}\n"
            msg += "-------------------------\n"
        await loading.edit_text(msg)
    except Exception as e:
        await loading.edit_text(f"❌ فشل الاتصال بقاعدة البيانات: {str(e)}")

async def handle_bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    if "العودة للقائمة الرئيسية" in text or text == "🏠 الرئيسية":
        user_data.clear()
        await update.message.reply_text("🔙 تم العودة للقائمة الرئيسية للخدمات:", reply_markup=get_main_keyboard())
        return

    elif "البكلوريا العلمي" in text or "تغيير المادة" in text:
        await update.message.reply_text("📚 اختر المادة التي ترغب بتصفح ملفاتها بالأيقونات الرسومية المحدثة الأنيقة:", reply_markup=get_subjects_keyboard())
        return

    elif "طلب إعلان" in text or "تواصل مع الإدارة" in text:
        await update.message.reply_text(f"💬 يمكنك التواصل مباشرة مع إدارة المكتبة والموقع عبر الحساب الرسمي التالي:\n\n🔗 @{YOUR_TELEGRAM_USERNAME}")
        return

    # فحص إذا كان النص المكتوب هو اسم قارئ تم اختياره مسبقاً
    if "audio_files" in user_data and "active_audio_category" in user_data:
        audio_files = user_data["audio_files"]
        category_code = user_data["active_audio_category"]
        
        # تصفية الملفات التي تطابق القارئ الذي ضغط عليه الطالب
        matching_files = []
        for f in audio_files:
            r_name = f.get("reciter") or f.get("teacher") or f.get("author") or f.get("description") or "قارئ عام"
            if text == f"🎙️ {r_name}":
                matching_files.append(f)
        
        if matching_files:
            loading_msg = await update.message.reply_text(f"⏳ جاري إرسال التسجيلات الصوتية بصوت ({text})...")
            for f in matching_files:
                try:
                    file_name = f.get("file_name") or f.get("title") or f.get("name") or "ملف صوتي"
                    caption_text = f"🔊 {file_name}"
                    f_id = f.get("file_id") or f.get("telegram_file_id")
                    f_url = f.get("file_url") or f.get("url") or f.get("file_path") or f.get("pdf_url")
                    
                    if f_id:
                        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f_id, caption=caption_text)
                    elif f_url:
                        try:
                            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f_url, caption=caption_text)
                        except Exception:
                            await update.message.reply_text(f"{caption_text}\n\n🔗 رابط التحميل:\n{f_url}")
                except Exception:
                    continue
            try:
                await loading_msg.delete()
            except Exception:
                pass
            return

    # فحص المادة المحددة
    matched_subject = None
    for k in SUBJECTS.keys():
        pure_subject_name = k.replace("📐","").replace("⚡","").replace("🧲","").replace("🧪","").replace("🧬","").replace("🕋","").replace("📚","").replace("🇬🇧","").replace("🇫🇷","").strip()
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
        # تنظيف بيانات القراء القديمة عند العودة
        user_data.pop("audio_files", None)
        user_data.pop("active_audio_category", None)
        subject_name = user_data["current_subject_name"]
        await update.message.reply_text(f"📂 تم العودة لقائمة أقسام مادة:\n🎯 {subject_name}", reply_markup=get_categories_keyboard(subject_name))
        return

    # 🌟 خريطة التصنيفات المحدثة ("كاملة" لتطابق التعديل الجديد)
    cat_map = {
        "حسب السنة": "exams_year",
        "كاملة": "exams_full",
        "حسب الأبحاث": "exams_topic",
        "الملخصات": "summaries",
        "الكتاب المدرسي": "textbook",  
        "النوط": "booklets",
        "ملاحظات": "notes",
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
        loading_msg = await update.message.reply_text("⏳ جاري فحص وتصفح الرفوف الدراسية...")
        
        files_list = []
        try:
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

        except Exception:
            await loading_msg.edit_text("⚠️ عذراً، واجهنا مشكلة مؤقتة في جلب البيانات، يرجى المحاولة لاحقاً.")
            return
        
        if not files_list:
            await loading_msg.edit_text(f"⚠️ لا توجد ملفات مرفوعة حالياً في قسم ({text}) لمادة {subject_name}.")
            return

        # 🎙️ ميزة فرز القراء الخاصة بالملفات الصوتية (الآيات والأحاديث)
        if matched_category_code in ["hadith_audio", "quran_audio"]:
            unique_reciters = set()
            for f in files_list:
                # يقرأ اسم القارئ من الأعمدة المحتملة في السيرفر لضمان المرونة الكاملة
                r_name = f.get("reciter") or f.get("teacher") or f.get("author") or f.get("description") or "قارئ عام"
                unique_reciters.add(r_name)
            
            # حفظ الملفات في الجلسة لاستدعائها فور الضغط على زر القارئ
            user_data["audio_files"] = files_list
            user_data["active_audio_category"] = matched_category_code
            
            # بناء كيبورد أزرار القراء ديناميكياً
            reciter_buttons = []
            reciters_list = sorted(list(unique_reciters))
            for i in range(0, len(reciters_list), 2):
                row = [f"🎙️ {name}" for name in reciters_list[i:i+2]]
                reciter_buttons.append(row)
            reciter_buttons.append(["🔙 العودة لأقسام المادة"])
            
            await loading_msg.delete()
            await update.message.reply_text(
                "🎙️ اختر القارئ المطلوب للاستماع إلى التسجيلات المقررة:",
                reply_markup=ReplyKeyboardMarkup(reciter_buttons, resize_keyboard=True)
            )
            return

        # إرسال الملفات العادية مباشرة (كتيبات، نوط، كتب...) إذا لم تكن مواداً صوتية
        try:
            await loading_msg.delete()
        except Exception:
            pass
        
        for f in files_list:
            try:
                file_name = f.get("file_name") or f.get("title") or f.get("name") or "ملف تعليمي"
                caption_text = f"📄 {file_name}"
                
                f_id = f.get("file_id") or f.get("telegram_file_id")
                f_url = f.get("file_url") or f.get("url") or f.get("file_path") or f.get("pdf_url")
                
                if f_id:
                    await context.bot.send_document(chat_id=update.effective_chat.id, document=f_id, caption=caption_text)
                elif f_url:
                    try:
                        await context.bot.send_document(chat_id=update.effective_chat.id, document=f_url, caption=caption_text)
                    except Exception:
                        await update.message.reply_text(f"{caption_text}\n\n🔗 رابط التحميل المباشر:\n{f_url}")
            except Exception:
                continue
        return

    await update.message.reply_text("ℹ️ من فضلك، استخدم أزرار القائمة السفلية الظاهرة أمامك للتنقل.", reply_markup=get_main_keyboard())

async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("debug", debug_database))
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
    
