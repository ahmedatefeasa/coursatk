import os
import json
import telebot
from telebot import types
import google.generativeai as genai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ADMIN_ID = 7666190050

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

DB_FILE = "custom_responses.json"
user_states = {}  # لتتبع خطوة الإضافة

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
# 🔘 لوحة التحكم بالأزرار (للأدمن)
# ---------------------------------------------------------

def get_admin_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn_add = types.InlineKeyboardButton("➕ إضافة رد جديد", callback_data="add_btn")
    btn_list = types.InlineKeyboardButton("📋 عرض كل الردود", callback_data="list_btn")
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
# 🕹️ التفاعل مع الأزرار
# ---------------------------------------------------------

@bot.callback_query_handler(func=lambda call: True)
def handle_clicks(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "عذراً، هذه اللوحة للأدمن فقط.")
        return

    if call.data == "add_btn":
        user_states[call.from_user.id] = {"step": "waiting_key"}
        bot.send_message(call.message.chat.id, "📝 ابعت دلوقتي **الكلمة أو الرسالة** اللي لما المستخدم يبعتها البوت يرُد عليها (مثلاً: كا):")
        bot.answer_callback_query(call.id)

    elif call.data == "list_btn":
        if not responses:
            bot.send_message(call.message.chat.id, "📭 لا توجد ردود محفوظة حتى الآن.")
        else:
            msg = "📋 **الردود المحفوظة حالياً:**\n\n"
            markup = types.InlineKeyboardMarkup()
            for k in responses.keys():
                msg += f"• `{k}` ⬅️ {responses[k]}\n"
                # زر حذف لكل كلمة
                markup.add(types.InlineKeyboardButton(f"❌ حذف '{k}'", callback_data=f"del_{k}"))
            bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("del_"):
        key_to_delete = call.data.replace("del_", "", 1)
        if key_to_delete in responses:
            del responses[key_to_delete]
            save_responses(responses)
            bot.send_message(call.message.chat.id, f"🗑️ تم حذف الرد الخاص بـ: '{key_to_delete}' بنجاح!")
        bot.answer_callback_query(call.id)

# ---------------------------------------------------------
# 💬 معالجة النصوص وحالة الإضافة (محادثة خطوة بخطوة)
# ---------------------------------------------------------

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    user_text = message.text.strip()

    # 1. إذا كان الأدمن في مرحلة إضافة رد (خطوة بخطوة)
    if user_id in user_states:
        state = user_states[user_id]
        
        # الخطوة الأولى: استلام الكلمة المفتاحية
        if state["step"] == "waiting_key":
            user_states[user_id] = {"step": "waiting_value", "key": user_text}
            bot.reply_to(message, f"تمام! الكلمة هي: **{user_text}**\n\nدلوقتي ابعت **الرد** اللي عاوز البوت يرُد بيه عليها:")
            return

        # الخطوة الثانية: استلام الرد وحفظه
        elif state["step"] == "waiting_value":
            key = state["key"]
            value = user_text
            responses[key] = value
            save_responses(responses)
            
            # إنهاء حالة الإضافة
            del user_states[user_id]
            
            bot.reply_to(
                message, 
                f"✅ **تم الحفظ بنجاح!**\n\n🔹 لما حد يبعت: `{key}`\n🔹 البوت هيرد بـ: `{value}`", 
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
            return

    # 2. البحث في الردود المحفوظة
    if user_text in responses:
        bot.reply_to(message, responses[user_text])
        return

    # 3. إرسال لـ Gemini في حالة عدم وجود رد مخزن
    try:
        prompt = f"أنت مساعد منصة كورسَاتِك التعليمية. أجب باختصار على: {user_text}"
        res = model.generate_content(prompt)
        bot.reply_to(message, res.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "حدث خطأ بسيط أثناء معالجة رسالتك، حاول مرة أخرى.")

print("Bot is running...")
bot.infinity_polling()
