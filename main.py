import os
import json
import telebot
from telebot import types
import google.generativeai as genai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ADMIN_ID = 7666190050

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# إعداد Gemini لو المفتاح موجود
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

DB_FILE = "custom_responses.json"
user_states = {}

def load_responses():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_responses(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

responses = load_responses()

# ---------------------------------------------------------
# 🔘 لوحة التحكم الرئيسية (للأدمن)
# ---------------------------------------------------------

def get_admin_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn_add = types.InlineKeyboardButton("➕ إضافة رد جديد", callback_data="add_btn")
    btn_list = types.InlineKeyboardButton("📋 عرض وتعديل الردود", callback_data="list_btn")
    markup.add(btn_add, btn_list)
    return markup

@bot.message_handler(commands=['start', 'admin'])
def send_welcome(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id, 
            "أهلاً بك يا أدمن! ⚙️\nاختر من الأزرار بالأسفل لإدارة ردود البوت:", 
            reply_markup=get_admin_keyboard()
        )
    else:
        bot.reply_to(message, "مرحباً بك في منصة كورسَاتِك! كيف يمكنني مساعدتك اليوم؟ 🎓")

# ---------------------------------------------------------
# 🕹️ التفاعل مع الأزرار القوائم والتعديل/الحذف
# ---------------------------------------------------------

@bot.callback_query_handler(func=lambda call: True)
def handle_clicks(call):
    global responses
    responses = load_responses()

    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "عذراً، هذه اللوحة للأدمن فقط.")
        return

    # 1. زر إضافة رد
    if call.data == "add_btn":
        user_states[call.from_user.id] = {"step": "waiting_key"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 إلغاء ورجوع", callback_data="back_main"))
        bot.edit_message_text(
            "📝 ابعت دلوقتي **الكلمة أو الرسالة** اللي عاوز البوت يرُد عليها:", 
            call.message.chat.id, 
            call.message.message_id, 
            parse_mode="Markdown",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    # 2. عرض قائمة الردود كـ أزرار
    elif call.data == "list_btn":
        if not responses:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 رجوع للوحة الرئيسية", callback_data="back_main"))
            bot.edit_message_text("📭 لا توجد ردود محفوظة حتى الآن.", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            for key in responses.keys():
                markup.add(types.InlineKeyboardButton(f"📌 {key}", callback_data=f"view_{key}"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع للوحة الرئيسية", callback_data="back_main"))
            
            bot.edit_message_text(
                "📋 **قائمة الردود المحفوظة:**\nاضغط على أي كلمة لتعديلها أو حذفها:", 
                call.message.chat.id, 
                call.message.message_id, 
                parse_mode="Markdown", 
                reply_markup=markup
            )
        bot.answer_callback_query(call.id)

    # 3. عرض تفاصيل رد معين (تعديل / حذف / رجوع)
    elif call.data.startswith("view_"):
        key = call.data.replace("view_", "", 1)
        if key in responses:
            val = responses[key]
            markup = types.InlineKeyboardMarkup()
            btn_edit = types.InlineKeyboardButton("✏️ تعديل الرد", callback_data=f"edit_{key}")
            btn_del = types.InlineKeyboardButton("🗑️ حذف الرد", callback_data=f"del_{key}")
            btn_back = types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="list_btn")
            markup.add(btn_edit, btn_del)
            markup.add(btn_back)

            bot.edit_message_text(
                f"⚙️ **تفاصيل الرد:**\n\n🔹 **الكلمة:** `{key}`\n🔹 **الرد الحالي:** `{val}`", 
                call.message.chat.id, 
                call.message.message_id, 
                parse_mode="Markdown", 
                reply_markup=markup
            )
        bot.answer_callback_query(call.id)

    # 4. بدء تعديل الرد
    elif call.data.startswith("edit_"):
        key = call.data.replace("edit_", "", 1)
        user_states[call.from_user.id] = {"step": "waiting_edit_value", "key": key}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 إلغاء ورجوع", callback_data=f"view_{key}"))
        
        bot.edit_message_text(
            f"✏️ اكتب **الرد الجديد** للكلمة: `{key}`", 
            call.message.chat.id, 
            call.message.message_id, 
            parse_mode="Markdown", 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    # 5. حذف الرد
    elif call.data.startswith("del_"):
        key = call.data.replace("del_", "", 1)
        if key in responses:
            del responses[key]
            save_responses(responses)
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="list_btn"))
            bot.edit_message_text(f"🗑️ تم حذف الرد الخاص بـ `{key}` بنجاح!", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    # 6. زر العودة للوحة الرئيسية
    elif call.data == "back_main":
        if call.from_user.id in user_states:
            del user_states[call.from_user.id]
        bot.edit_message_text("أهلاً بك يا أدمن! ⚙️\nاختر من الأزرار بالأسفل لإدارة ردود البوت:", call.message.chat.id, call.message.message_id, reply_markup=get_admin_keyboard())
        bot.answer_callback_query(call.id)

# ---------------------------------------------------------
# 💬 معالجة تمام الرسائل العامة
# ---------------------------------------------------------

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global responses
    user_id = message.from_user.id
    user_text = message.text.strip() if message.text else ""

    if not user_text:
        return

    # 1. معالجة حالات الأدمن (إضافة جديدة أو تعديل)
    if user_id == ADMIN_ID and user_id in user_states:
        state = user_states[user_id]
        
        if state["step"] == "waiting_key":
            user_states[user_id] = {"step": "waiting_value", "key": user_text}
            bot.reply_to(message, f"تمام! الكلمة هي: **{user_text}**\n\nدلوقتي ابعت **الرد** اللي عاوز البوت يرُد بيه:")
            return

        elif state["step"] == "waiting_value":
            key = state["key"]
            responses[key] = user_text
            save_responses(responses)
            del user_states[user_id]
            bot.reply_to(message, f"✅ **تم الحفظ بنجاح!**\n\n🔹 عند إرسال: `{key}`\n🔹 سيرد البوت بـ: `{user_text}`", parse_mode="Markdown", reply_markup=get_admin_keyboard())
            return

        elif state["step"] == "waiting_edit_value":
            key = state["key"]
            responses[key] = user_text
            save_responses(responses)
            del user_states[user_id]
            bot.reply_to(message, f"✅ **تم تحديث الرد بنجاح!**\n\n🔹 الكلمة: `{key}`\n🔹 الرد الجديد: `{user_text}`", parse_mode="Markdown", reply_markup=get_admin_keyboard())
            return

    # 2. قراءة أحدث الردود
    responses = load_responses()

    # 3. البحث المرن في الردود المحفوظة (حساب المسافات وحالة الأحرف)
    clean_user_text = user_text.lower()
    for stored_key, stored_val in responses.items():
        if stored_key.strip().lower() == clean_user_text:
            bot.reply_to(message, stored_val)
            return

    # 4. إجابة Gemini للأسئلة العامة
    try:
        if model:
            prompt = f"أنت مساعد منصة كورسَاتِك التعليمية. أجب باختصار على: {user_text}"
            res = model.generate_content(prompt)
            if res.text:
                bot.reply_to(message, res.text)
            else:
                bot.reply_to(message, "مرحباً بك في كورسَاتِك! كيف يمكنني مساعدتك؟")
        else:
            bot.reply_to(message, "مرحباً بك في منصة كورسَاتِك! 🎓")
    except Exception as e:
        print(f"Gemini Error: {e}")
        bot.reply_to(message, "مرحباً بك في منصة كورسَاتِك! كيف يمكنني مساعدتك اليوم؟ 🎓")

print("Bot is running...")
bot.infinity_polling(skip_pending=True)
