import os
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from supabase import create_client

# --- إعدادات ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 1. ميزة الإعلانات (كما كانت في كودك السابق) ---
async def broadcast_announcement(context: ContextTypes.DEFAULT_TYPE):
    try:
        response = supabase.table("announcements").select("*").eq("is_sent", False).execute()
        if not response.data: return
        students = supabase.table("students").select("telegram_id").execute()
        for ann in response.data:
            msg = ann['message']
            for student in students.data:
                try:
                    await context.bot.send_message(chat_id=student['telegram_id'], text=f"📢 <b>إعلان:</b>\n\n{msg}", parse_mode="HTML")
                    await asyncio.sleep(0.05)
                except: continue
            supabase.table("announcements").update({"is_sent": True}).eq("id", ann['id']).execute()
    except Exception as e: logger.error(f"Error broadcasting: {e}")

# --- 2. ميزة التقاط الملفات (كما كانت) ---
async def catch_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    f_id = msg.document.file_id if msg.document else msg.audio.file_id
    await msg.reply_text(f"✅ تم التقاط المعرف:\n<code>{f_id}</code>", parse_mode="HTML")

# --- 3. النظام الشجري الديناميكي (الجديد) ---
async def get_menu_items(parent_id=None):
    query = supabase.table("menu_items").select("*").order("order_index")
    if parent_id:
        query = query.eq("parent_id", parent_id)
    else:
        query = query.is_("parent_id", "null")
    return query.execute().data

async def show_menu(update, context, parent_id=None):
    items = await get_menu_items(parent_id)
    keyboard = []
    row = []
    for item in items:
        row.append(KeyboardButton(item['label']))
        if len(row) == 2:
            keyboard.append(row); row = []
    if row: keyboard.append(row)
    
    # أزرار تحكم
    footer = []
    if parent_id: footer.append("🔙 العودة للخلف")
    footer.append("🏠 الرئيسية")
    keyboard.append(footer)

    await update.message.reply_text("📂 اختر من القائمة:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle_bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data
    
    # منطق التنقل
    if text == "🏠 الرئيسية":
        user_data["current_node"] = None
        await show_menu(update, context, None)
        return
        
    if text == "🔙 العودة للخلف":
        current = user_data.get("current_node")
        parent = supabase.table("menu_items").select("parent_id").eq("id", current).single().execute().data
        parent_id = parent.get("parent_id") if parent else None
        user_data["current_node"] = parent_id
        await show_menu(update, context, parent_id)
        return

    # التحقق من الضغط على زر
    current_node = user_data.get("current_node")
    items = await get_menu_items(current_node)
    selected = next((i for i in items if i['label'] == text), None)

    if selected:
        if selected['type'] == 'folder':
            user_data["current_node"] = selected['id']
            await show_menu(update, context, selected['id'])
        else:
            # إرسال الملف
            caption = f"📎 {selected['label']}"
            if selected['telegram_file_id']:
                await update.message.reply_document(document=selected['telegram_file_id'], caption=caption)
            elif selected['content_url']:
                await update.message.reply_document(document=selected['content_url'], caption=caption)
    else:
        await update.message.reply_text("ℹ️ استخدم القائمة للتنقل.")

def main():
    app = Application.builder().token(os.environ.get("BOT_TOKEN")).build()
    
    # المهام المجدولة
    app.job_queue.run_repeating(broadcast_announcement, interval=3600, first=10)
    
    # المعالجات
    app.add_handler(CommandHandler("start", lambda u, c: show_menu(u, c, None)))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.AUDIO, catch_file_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_logic))
    
    app.run_polling()

if __name__ == "__main__":
    main()
    
