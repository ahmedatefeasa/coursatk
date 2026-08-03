import os
import telebot
import google.generativeai as genai

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="أنت مساعد لخدمة العملاء لمنصة كورساتك (Coursatk). رد على استفسارات الطلاب بأسلوب ودود واحترافي، وإذا طلبوا الاشتراك وجههم للرابط coursatk.online/subscribe."
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {e}")

print("Bot is running...")
bot.infinity_polling()
