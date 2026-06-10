import os
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from supabase import create_client

# --- إعداد السجلات لمنع الكراش الصامت ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

YOUR_TELEGRAM_USERNAME = "Yousef55641"

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

# --- 3. ميزة التقاط معرف الملف للمدير (صافي تماماً بدون أي نص إضافي) ---
# --- 3. ميزة التقاط معرف الملف/الصورة للمدير (محدثة لدعم الصور) ---
async def catch_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    f_id = None
    
    # التقاط معرف المستند
    if msg.document:
        f_id = msg.document.file_id
    # التقاط معرف الملف الصوتي
    elif msg.audio:
        f_id = msg.audio.file_id
    # التقاط معرف الصورة (نأخذ آخر عنصر في القائمة لأنه صاحب الجودة الأعلى)
    elif msg.photo:
        f_id = msg.photo[-1].file_id
        
    if f_id:
        # إرسال المعرف صافياً تماماً
        await msg.reply_text(f"<code>{f_id}</code>", parse_mode="HTML")


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
    
    # توزيع الأزرار بشكل ثنائي
    row = []
    for item in items:
        row.append(KeyboardButton(item['label']))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: 
        keyboard.append(row)
    
    # إضافة الأزرار الثابتة (نشر إعلان) فقط في القائمة الرئيسية (عندما يكون parent_id هو None)
    if parent_id is None:
        keyboard.append([KeyboardButton("📢 نشر إعلان")])
    
    # إضافة أزرار التحكم في أسفل القائمة
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

# --- 7. المعالج الرئيسي لمنطق البوت الشجري ---
async def handle_bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    # ميزة زر نشر إعلان الثابت
    if text == "📢 نشر إعلان":
        announcement_msg = (
            "✨ <b>مرحباً بك عزيزي الطالب في قسم الدعم والإعلانات</b> ✨\n\n"
            "لطلب الإعلانات، الاستفسارات، أو التواصل المباشر مع إدارة المكتبة والموقع، "
            "يسعدنا تواصلك معنا مباشرة عبر الحساب الرسمي التالي:\n\n"
            "🔗 <b>حساب التواصل الرسمي:</b> @Yousef55641\n\n"
            "📥 <i>اضغط على المعرف أعلاه لبدء المحادثة فوراً، وسنقوم بالرد عليك في أقرب وقت ممكن.</i>"
        )
        await update.message.reply_text(announcement_msg, parse_mode="HTML")
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
            # فحص إذا كان المجلد فارغاً قبل تحويل جلسة المستخدم إليه (حل مشكلة التعليق)
            sub_items = await get_menu_items(selected['id'])
            if not sub_items:
                await update.message.reply_text(f"⚠️ لا توجد محتويات أو ملفات مرفوعة حالياً في قسم ({text}).")
                # نبقي المستخدم في نفس مكانه دون تغيير current_node
                return
            
            # إذا لم يكن فارغاً، ننتقل بأمان
            user_data["current_node"] = selected['id']
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

    application.add_handler(CommandHandler("start", start))
    # في دالة main، ابحث عن سطر معالجة الملفات وقم بتعديله ليصبح هكذا:
    application.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO | filters.PHOTO, catch_file_id))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))

    logger.info("🚀 البوت الشجري المعدل مستقر ويعمل الآن بدون أي مشاكل تعليق...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
