import os
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
)
from supabase import create_client
from pypdf import PdfReader, PdfWriter

# --- إعداد السجلات لمنع الكراش الصامت ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# مسار ملف الغلاف الثابت الذي صممته على كانفا وسيكون مخزناً على السيرفر بنفس المجلد
COVER_PATH = "cover.pdf"
# ضع الآيدي (ID) الخاص بك كأدمن هنا لحماية الميزة (تأكد من كتابة الآيدي الخاص بك)
ADMIN_ID = 123456789  

# --- دالة مساعدة لمعالجة دمج ملفات الـ PDF ---
def process_pdf_geometry(mode, original_path, output_path):
    writer = PdfWriter()
    if mode == "add":
        writer.append(COVER_PATH)
        writer.append(original_path)
    elif mode == "replace":
        writer.append(COVER_PATH)
        reader = PdfReader(original_path)
        for page_num in range(1, len(reader.pages)):
            writer.add_page(reader.pages[page_num])
    
    with open(output_path, "wb") as f:
        writer.write(f)

# --- 1. ميزة الإعلانات التلقائية (من قاعدة البيانات) ---
async def broadcast_announcement(context: ContextTypes.DEFAULT_TYPE):
    try:
        response = supabase.table("announcements").select("*").eq("is_sent", False).execute()
        if not response.data: 
            return

        students = supabase.table("students").select("telegram_id").execute()
        
        for ann in response.data:
            msg = ann['message']
            for student in students.data:
                try:
                    await context.bot.send_message(chat_id=student['telegram_id'], text=f"📢 <b>إعلان من المكتبة:</b>\n\n{msg}", parse_mode="HTML")
                    await asyncio.sleep(0.05)
                except:
                    continue
            
            supabase.table("announcements").update({"is_sent": True}).eq("id", ann['id']).execute()
            logger.info(f"تم بث الإعلان رقم {ann['id']} بنجاح.")
    except Exception as e:
        logger.error(f"خطأ في نظام الإعلانات: {e}")

# --- 2. ميزة تسجيل الطلاب ---
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

# --- 3. ميزة التقاط وتعديل ملفات المدير مع الغلاف الذكي ---
async def catch_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # التحقق أولاً إذا كان المرسل هو الأدمن
    if user_id == ADMIN_ID:
        # حالة 1: الملف المرفوع مستند PDF (تطبيق منطق الغلاف الذكي)
        if update.message.document and update.message.document.mime_type == "application/pdf":
            loading_msg = await update.message.reply_text("⏳ جاري تحميل مستند الـ PDF لتجهيز خيارات الغلاف...")
            
            # تحميل الملف مؤقتاً إلى السيرفر
            file = await context.bot.get_file(update.message.document.file_id)
            input_filename = f"temp_{update.message.chat_id}.pdf"
            await file.download_to_drive(input_filename)
            await loading_msg.delete()

            # حفظ المسار المؤقت في ذاكرة البوت
            context.user_data["temp_pdf_path"] = input_filename

            # إنشاء لوحة تحكم تفاعلية مدمجة (Inline Buttons)
            keyboard = [
                [InlineKeyboardButton("➕ إضافة الغلاف كصفحة أولى", callback_data="cover_add")],
                [InlineKeyboardButton("🔄 استبدال الصفحة الأولى الحالية", callback_data="cover_replace")],
                [InlineKeyboardButton("⏩ تخطي وإرسال المعرف الحالي فوراً", callback_data="cover_skip")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("🎯 تم التقاط ملف PDF. اختر الإجراء المناسب لغلاف المكتبة التعليمية:", reply_markup=reply_markup)
            return

        # حالة 2: المرفق عبارة عن صورة (Photo) - إرسال المعرف فوراً
        elif update.message.photo:
            # نأخذ أعلى جودة للصورة وهي دائماً آخر عنصر في القائمة
            f_id = update.message.photo[-1].file_id
            await update.message.reply_text(f"🖼️ تم التقاط معرف الصورة بنجاح!\n\n<code>{f_id}</code>", parse_mode="HTML")
            return

        # حالة 3: المرفق ملف صوتي (Audio) - إرسال المعرف فوراً
        elif update.message.audio:
            f_id = update.message.audio.file_id
            await update.message.reply_text(f"🔊 تم التقاط معرف الملف الصوتي بنجاح!\n\n<code>{f_id}</code>", parse_mode="HTML")
            return

        # حالة 4: أي مستند آخر ليس PDF (مثل الكليبات، الفيديوهات أو مستندات أخرى)
        elif update.message.document:
            f_id = update.message.document.file_id
            await update.message.reply_text(f"📄 تم التقاط معرف المستند بنجاح!\n\n<code>{f_id}</code>", parse_mode="HTML")
            return
            
    # إذا لم يكن المرسل هو الأدمن، يتم تجاهل المرفقات لكي لا تسبب تشتت للبوت الشجري

# معالج ضغطات الأزرار المدمجة للأدمن
async def handle_cover_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action = query.data
    user_data = context.user_data
    
    if action == "cover_skip":
        input_path = user_data.get("temp_pdf_path")
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
        user_data.clear()
        
        # إرجاع الـ file_id الأصلي مباشرة
        f_id = query.message.reply_to_message.document.file_id
        await query.edit_message_text(f"<code>{f_id}</code>", parse_mode="HTML")
        return

    # تخزين نوع العملية المطلوبة (add أو replace)
    user_data["cover_action"] = "add" if action == "cover_add" else "replace"
    
    # الانتقال لخطوة طلب اسم الملف الجديد
    user_data["awaiting_filename"] = True
    await query.edit_message_text("📝 ممتاز! الآن قم بكتابة وإرسال **اسم الملف الجديد** (بدون لاحقات، مثال: `كتاب الهندسة`):")

# --- 4. جلب القائمة من قاعدة البيانات ---
async def get_menu_items(parent_id=None):
    query = supabase.table("menu_items").select("*").order("order_index")
    if parent_id:
        query = query.eq("parent_id", parent_id)
    else:
        query = query.is_("parent_id", "null")
    res = query.execute()
    return res.data if res.data else []

# --- 5. دالة بناء وعرض الكيبورد الديناميكي ---
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, parent_id=None, text_message="يرجى اختيار القسم المطلوب من الأزرار بالأسفل:"):
    items = await get_menu_items(parent_id)
    keyboard = []
    
    row = []
    for item in items:
        row.append(KeyboardButton(item['label']))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: 
        keyboard.append(row)
    
    footer = []
    if parent_id:
        footer.append(KeyboardButton("🔙 العودة للخلف"))
    footer.append(KeyboardButton("🏠 القائمة الرئيسية"))
    keyboard.append(footer)

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(text_message, reply_markup=reply_markup)

# --- 6. رسالة البدء (/start) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await register_student_to_supabase(update.effective_user)
    context.user_data.clear() 
    welcome_text = "👋 أهلاً بك في بوت المكتبة التعليمية لطلاب البكالوريا العلمي.\n\nيرجى استخدام القائمة السفلية للتصفح السلس والمنظم للشجرة الدراسية:"
    await show_menu(update, context, parent_id=None, text_message=welcome_text)

# --- 7. المعالج الرئيسي لمنطق البوت الشجري واستقبل اسم الملف للمدير ---
async def handle_bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    # فحص إذا كان البوت ينتظر من الأدمن كتابة اسم الملف الجديد لدمجه
    if update.message.from_user.id == ADMIN_ID and user_data.get("awaiting_filename"):
        input_path = user_data.get("temp_pdf_path")
        mode = user_data.get("cover_action")
        
        if not input_path or not os.path.exists(input_path):
            await update.message.reply_text("❌ حدث خطأ، لم يتم العثور على الملف المؤقت. يرجى إعادة رفع الملف مجدداً.")
            user_data.clear()
            return
            
        # التأكد من لاحقة الملف لتظهر بشكل صحيح للطلاب
        custom_name = text if text.lower().endswith(".pdf") else f"{text}.pdf"
        output_path = f"ready_{custom_name}"
        
        prog_msg = await update.message.reply_text("⚙️ جاري معالجة وتعديل ملف الـ PDF وتطبيق الغلاف الحصري...")
        
        try:
            # دمج أو استبدال الصفحات مع الغلاف
            await asyncio.to_thread(process_pdf_geometry, mode, input_path, output_path)
            
            # إرسال الملف الجديد للأدمن بالاسم الجديد المحدد للالتقاط
            with open(output_path, "rb") as f:
                sent_doc = await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    caption=f"✅ تم تجهيز غلاف المكتبة بنجاح باسم:\n`{custom_name}`"
                )
            
            # إرسال معرف الملف فقط لتسهيل النسخ السريع بضغطة واحدة
            await update.message.reply_text(f"<code>{sent_doc.document.file_id}</code>", parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"خطأ أثناء معالجة ملف PDF للمدير: {e}")
            await update.message.reply_text("❌ حدث خطأ داخلي أثناء معالجة الملف وتوليده.")
        finally:
            # تنظيف السيرفر من الملفات المؤقتة فوراً
            if os.path.exists(prog_msg.message_id): await prog_msg.delete()
            if os.path.exists(input_path): os.remove(input_path)
            if os.path.exists(output_path): os.remove(output_path)
            user_data.clear()
        return

    # أزرار التنقل الثابتة
    if text == "🏠 القائمة الرئيسية":
        user_data.clear()
        await show_menu(update, context, parent_id=None, text_message="🔙 تم العودة للقائمة الرئيسية للخدمات:")
        return
        
    if text == "🔙 العودة للخلف":
        current = user_data.get("current_node")
        if current:
            parent_res = supabase.table("menu_items").select("parent_id").eq("id", current).single().execute()
            parent_id = parent_res.data.get("parent_id") if parent_res.data else None
            user_data["current_node"] = parent_id
            await show_menu(update, context, parent_id, text_message="تم العودة للخلف:")
        else:
            user_data.clear()
            await show_menu(update, context, parent_id=None)
        return

    # فحص الأزرار الديناميكية المتاحة في المجلد الحالي
    current_node = user_data.get("current_node")
    items = await get_menu_items(current_node)
    selected = next((i for i in items if i['label'] == text), None)

    if selected:
        if selected['type'] == 'folder':
            user_data["current_node"] = selected['id']
            sub_items = await get_menu_items(selected['id'])
            if not sub_items:
                await update.message.reply_text(f"⚠️ لا توجد محتويات أو ملفات مرفوعة حالياً في قسم ({text}).")
                return
            await show_menu(update, context, selected['id'], text_message=f"✨ لقد فتحت الآن رفوف:\n🎯 {text}")
        
        elif selected['type'] == 'text_msg':
            await update.message.reply_text(selected['content_url'], parse_mode="HTML")

        elif selected['type'] == 'file':
            loading_msg = await update.message.reply_text(f"⏳ جاري جلب وإرسال ملف ({text})...")
            
            caption_text = f"<b>📄 {selected['label']}</b>"
            f_id = selected.get("telegram_file_id")
            f_url = selected.get("content_url")
            
            success = False
            try:
                if f_id:
                    await context.bot.send_document(chat_id=update.effective_chat.id, document=f_id, caption=caption_text, parse_mode="HTML")
                    success = True
            except Exception as e:
                logger.warning(f"فشل الإرسال عبر file_id: {e}")
            
            if not success and f_url:
                try:
                    await context.bot.send_document(chat_id=update.effective_chat.id, document=f_url, caption=caption_text, parse_mode="HTML")
                    success = True
                except Exception as e:
                    logger.error(f"فشل الإرسال عبر الرابط: {e}")
            
            await loading_msg.delete()
            
            if not success:
                await update.message.reply_text("⚠️ عذراً، حدث خطأ أثناء محاولة تحميل هذا الملف، يرجى مراجعة الإدارة.")
    else:
        await update.message.reply_text("ℹ️ من فضلك، استخدم أزرار القائمة السفلية الظاهرة أمامك للتنقل.", reply_markup=ReplyKeyboardMarkup([["🏠 القائمة الرئيسية"]], resize_keyboard=True))

def main():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ BOT_TOKEN مفقود!")
        return

    application = Application.builder().token(bot_token).build()
    
    application.job_queue.run_repeating(broadcast_announcement, interval=3600, first=10)

    # معالجات البوت (تم تصحيح السطر المسبب للكراش بالكامل هنا)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_cover_callbacks, pattern="^cover_"))
    
    # التقاط كافة أنواع الميديا والصور والملفات من الأدمن للفحص والفرز الذكي
    application.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO | filters.PHOTO, catch_file_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))

    logger.info("🚀 البوت الشجري الاحترافي مستقر ويعمل الآن...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
