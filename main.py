import os
import json
import telebot
import google.generativeai as genai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ⚠️ حط هنا الـ ID بتاعك اللي جبته من userinfobot
ADMIN_ID = 123456789  # استبدل الرقم ده برقمك الحقيقي

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

DB_FILE = "custom_responses.json"

# تحميل الردود المحفوظة
def load_responses():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# حفظ الردود الجديدة
def save_responses(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

responses = load_responses()

# ---------------------------------------------------------
# 🛠️ أوانم الأدمن فقط (إضافة وحذف وعرض الردود)
# ---------------------------------------------------------

# أمر إضافة رد: /add الكلمة = الرد
@bot.message_handler(commands=['add'])
def add_response(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذا الأمر مخصص للأدمن فقط.")
        return
    
    try:
        # أخذ النص بعد كلمة /add
        text = message.text.replace("/add", "", 1).strip()
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        responses[key] = value
        save_responses(responses)
        bot.reply_to(message, f"✅ تم الحفظ بنجاح!\n\n**الكلمة:** {key}\n**الرد:** {value}")
    except Exception:
        bot.reply_to(message, "⚠️ صيغة الخاطئة! استخدم الأمر بالشكل ده:\n`/add كا = كا`\n(الكلمة = الرد)")

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
        bot.reply_to(message, "❌ الكلمة دي مش موجودة أصلاً.")

# أمر عرض كل الردود المحفوظة: /list
@bot.message_handler(commands=['list'])
def list_responses(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if not responses:
        bot.reply_to(message, "📭 مفيش أي ردود محفّظة حالياً.")
        return
    
    msg = "📋 **قائمة الردود المحفوظة:**\n\n"
    for k, v in responses.items():
        msg += f"• `{k}` ⬅️ {v}\n"
    bot.reply_to(message, msg, parse_mode="Markdown")

# ---------------------------------------------------------
# 💬 معالجة كافة الرسائل العامة
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_text = message.text.strip()
    
    # 1. البحث في الردود المحفوظة أولاً
    if user_text in responses:
        bot.reply_to(message, responses[user_text])
        return

    # 2. لو مش موجودة -> يجاوب بـ Gemini
    try:
        prompt = f"أنت مساعد منصة كورسَاتِك. أجب باختصار على: {user_text}"
        res = model.generate_content(prompt)
        bot.reply_to(message, res.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "حدث خطأ بسيط، حاول مرة أخرى.")

print("Bot starts working...")
bot.infinity_polling()
