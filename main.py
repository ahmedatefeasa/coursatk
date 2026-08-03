import os
import json
import telebot
import google.generativeai as genai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# تم وضع الـ ID الخاص بك كأدمن للبوت
ADMIN_ID = 7666190050

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

DB_FILE = "custom_responses.json"

# تحميل الردود المحفوظة
def load_responses():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# حفظ الردود الجديدة
def save_responses(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

responses = load_responses()

# ---------------------------------------------------------
# 🛠️ أوامر الأدمن (إضافة، حذف، عرض)
# ---------------------------------------------------------

# أمر إضافة رد: /add الكلمة = الرد
@bot.message_handler(commands=['add'])
def add_response(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذا الأمر مخصص للأدمن فقط.")
        return
    
    try:
        text = message.text.replace("/add", "", 1).strip()
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        responses[key] = value
        save_responses(responses)
        bot.reply_to(message, f"✅ **تم حفظ الرد بنجاح!**\n\n🔹 **عند إرسال:** {key}\n🔹 **سيرد البوت بـ:** {value}", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "⚠️ **صيغة غير صحيحة!**\nارسل الأمر بالشكل التالي:\n`/add كا = كا`", parse_mode="Markdown")

# أمر حذف رد: /del الكلمة
@bot.message_handler(commands=['del'])
def del_response(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    key = message.text.replace("/del", "", 1).strip()
    if key in responses:
        del responses[key]
        save_responses(responses)
        bot.reply_to(message, f"🗑️ تم حذف الرد الخاص بـ: '{key}'")
    else:
        bot.reply_to(message, "❌ هذه الكلمة غير موجودة في القائمة.")

# أمر عرض كل الردود: /list
@bot.message_handler(commands=['list'])
def list_responses(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if not responses:
        bot.reply_to(message, "📭 لا توجد أي ردود محفوظة حالياً.")
        return
    
    msg = "📋 **قائمة الردود المحفوظة:**\n\n"
    for k, v in responses.items():
        msg += f"• `{k}` ⬅️ {v}\n"
    bot.reply_to(message, msg, parse_mode="Markdown")

# ---------------------------------------------------------
# 💬 معالجة تمام الرسائل
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_text = message.text.strip()
    
    # 1. البحث في الردود المحفوظة أولاً
    if user_text in responses:
        bot.reply_to(message, responses[user_text])
        return

    # 2. إذا لم تكن موجودة -> يرسلها لـ Gemini
    try:
        prompt = f"أنت مساعد منصة كورسَاتِك التعليمية. أجب باختصار ووضوح على: {user_text}"
        res = model.generate_content(prompt)
        bot.reply_to(message, res.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "حدث خطأ بسيط في معالجة الطلب، حاول مرة أخرى.")

print("Bot is running...")
bot.infinity_polling()
