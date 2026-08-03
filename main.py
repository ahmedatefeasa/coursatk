import os
import json
import telebot

# التوكن الخاص ببوتك ومعرف حسابك الشخصي
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 7666190050  # معرف حسابك الشخصي كـ أدمن

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# مهم: لو مفعّل عندك Volume في Railway، خلي المسار جوه الـ Volume
# عشان الردود متضيعش مع كل Deploy أو Restart
# مثال: DB_FILE = "/app/data/responses.json"
DB_FILE = "/app/data/responses.json"

# دالة تحميل الردود المخزنة
def load_responses():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


# دالة حفظ الردود
def save_responses(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


responses = load_responses()

# ----------------- 1. لوحة تحكم الأدمن (في شات البوت) -----------------

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id == ADMIN_ID:
        msg = (
            "⚙️ **لوحة التحكم في الردود التلقائية (Business Bot)**\n\n"
            "📌 **لإضافة رد جديد أرسل:**\n"
            "`إضافة: الكلمة المفتاحية = الرد المطلوب`\n\n"
            "💡 **مثال:**\n"
            "`إضافة: كورس بايثون = تفضل التفاصيل ورابط التسجيل: https://example.com`\n\n"
            "❌ **لحذف رد أرسل:**\n"
            "`حذف: الكلمة المفتاحية`\n\n"
            "📋 **لعرض جميع الردود اكتب:** `عرض الردود`"
        )
        bot.reply_to(message, msg, parse_mode="Markdown")
    else:
        bot.reply_to(message, "مرحباً بك! هذا البوت مخصص لإدارة الردود التلقائية.")


# إضافة رد جديد
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text and m.text.startswith("إضافة:"))
def add_response(message):
    global responses
    try:
        content = message.text.replace("إضافة:", "").strip()
        key, value = content.split("=", 1)
        key = key.strip().lower()
        value = value.strip()

        responses[key] = value
        save_responses(responses)
        bot.reply_to(
            message,
            f"✅ **تم حفظ الرد بنجاح!**\n\n🔑 **الكلمة:** `{key}`\n💬 **الرد:** {value}",
            parse_mode="Markdown"
        )
    except Exception:
        bot.reply_to(
            message,
            "❌ **صيغة خاطئة!** استخدم الشكل التالي:\n`إضافة: الكلمة = الرد المطلوب`",
            parse_mode="Markdown"
        )


# حذف رد
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text and m.text.startswith("حذف:"))
def delete_response(message):
    global responses
    key = message.text.replace("حذف:", "").strip().lower()
    if key in responses:
        del responses[key]
        save_responses(responses)
        bot.reply_to(message, f"🗑️ تم حذف الرد الخاص بـ `{key}` بنجاح.", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"⚠️ الكلمة `{key}` غير موجودة في القائمة.", parse_mode="Markdown")


# عرض الردود
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "عرض الردود")
def list_responses(message):
    current = load_responses()
    if not current:
        bot.reply_to(message, "📭 لا توجد ردود مخزنة حالياً.")
        return

    text = "📋 **الردود المخزنة حالياً:**\n\n"
    for k, v in current.items():
        text += f"🔹 `{k}` 💬 {v}\n"
    bot.reply_to(message, text, parse_mode="Markdown")


# ----------------- 2. الرد التلقائي في محادثات الأعمال (شاتك الشخصي) -----------------

@bot.business_message_handler(func=lambda message: True)
def handle_business_message(business_message):
    try:
        global responses
        responses = load_responses()

        user_text = business_message.text
        if not user_text:
            return

        clean_text = user_text.strip().lower()

        # فحص الكلمات المفتاحية والرد بالنيابة عنك
        for key, val in responses.items():
            if key in clean_text:
                bot.send_message(
                    chat_id=business_message.chat.id,
                    text=val,
                    business_connection_id=business_message.business_connection_id
                )
                break
    except Exception as e:
        print(f"Error handling business message: {e}")


# ----------------- التشغيل -----------------

if __name__ == "__main__":
    # مهم جداً: بيمسح أي Webhook قديم متسجل على التوكن
    # عشان يمنع تعارض 409 مع الـ polling
    bot.remove_webhook()

    print("🚀 Coursatk Business Bot is online & running...")
    bot.infinity_polling()
