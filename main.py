import os
import json
import telebot
from telebot import types

# التوكن الخاص ببوتك ومعرف حسابك الشخصي
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 7666190050  # معرف حسابك الشخصي كـ أدمن

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# لازم يكون فيه Volume متربط ومعمول له Mount Path = /app/data
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


# ----------------- القائمة الرئيسية بالأزرار -----------------

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة رد جديد", callback_data="add"),
        types.InlineKeyboardButton("✏️ تعديل رد", callback_data="edit_menu"),
        types.InlineKeyboardButton("🗑️ حذف رد", callback_data="delete_menu"),
        types.InlineKeyboardButton("📋 عرض كل الردود", callback_data="list"),
    )
    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            "⚙️ **لوحة التحكم في الردود التلقائية**\n\nاختار من الأزرار تحت:",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    else:
        bot.reply_to(message, "مرحباً بك! هذا البوت مخصص لإدارة الردود التلقائية.")


# ----------------- التعامل مع ضغط الأزرار -----------------

@bot.callback_query_handler(func=lambda call: call.from_user.id == ADMIN_ID)
def handle_callback(call):
    global responses

    if call.data == "add":
        msg = bot.send_message(call.message.chat.id, "✏️ ابعتلي الكلمة المفتاحية اللي عاوز تضيفها:")
        bot.register_next_step_handler(msg, process_add_key)
        bot.answer_callback_query(call.id)

    elif call.data == "list":
        responses = load_responses()
        if not responses:
            bot.send_message(call.message.chat.id, "📭 لا توجد ردود مخزنة حالياً.", reply_markup=main_menu())
        else:
            text = "📋 **الردود المخزنة حالياً:**\n\n"
            for k, v in responses.items():
                text += f"🔹 `{k}` 💬 {v}\n"
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
        bot.answer_callback_query(call.id)

    elif call.data == "edit_menu":
        responses = load_responses()
        if not responses:
            bot.send_message(call.message.chat.id, "📭 لا توجد ردود لتعديلها.", reply_markup=main_menu())
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for k in responses.keys():
                markup.add(types.InlineKeyboardButton(f"✏️ {k}", callback_data=f"edit:{k}"))
            markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
            bot.send_message(call.message.chat.id, "اختار الرد اللي عاوز تعدله:", reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("edit:"):
        key = call.data.replace("edit:", "", 1)
        responses = load_responses()
        if key not in responses:
            bot.send_message(call.message.chat.id, "⚠️ الرد ده مش موجود.", reply_markup=main_menu())
        else:
            msg = bot.send_message(
                call.message.chat.id,
                f"✏️ الرد الحالي لـ `{key}` هو:\n{responses[key]}\n\nابعتلي الرد الجديد:",
                parse_mode="Markdown"
            )
            bot.register_next_step_handler(msg, process_edit_value, key)
        bot.answer_callback_query(call.id)

    elif call.data == "delete_menu":
        responses = load_responses()
        if not responses:
            bot.send_message(call.message.chat.id, "📭 لا توجد ردود لحذفها.", reply_markup=main_menu())
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for k in responses.keys():
                markup.add(types.InlineKeyboardButton(f"🗑️ {k}", callback_data=f"del:{k}"))
            markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
            bot.send_message(call.message.chat.id, "اختار الرد اللي عاوز تحذفه:", reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("del:"):
        key = call.data.replace("del:", "", 1)
        responses = load_responses()
        if key in responses:
            del responses[key]
            save_responses(responses)
            bot.send_message(
                call.message.chat.id,
                f"✅ تم حذف `{key}` بنجاح.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(call.message.chat.id, "⚠️ الرد ده اتحذف قبل كدة.", reply_markup=main_menu())
        bot.answer_callback_query(call.id)

    elif call.data == "back":
        bot.send_message(
            call.message.chat.id,
            "⚙️ **لوحة التحكم**",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        bot.answer_callback_query(call.id)


def process_add_key(message):
    if message.from_user.id != ADMIN_ID:
        return
    key = message.text.strip().lower()
    msg = bot.send_message(
        message.chat.id,
        f"تمام، دلوقتي ابعتلي الرد اللي هيتبعت لما حد يكتب: `{key}`",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_add_value, key)


def process_add_value(message, key):
    if message.from_user.id != ADMIN_ID:
        return
    global responses
    value = message.text.strip()
    responses = load_responses()
    responses[key] = value
    save_responses(responses)
    bot.send_message(
        message.chat.id,
        f"✅ **تم الحفظ بنجاح!**\n\n🔑 الكلمة: `{key}`\n💬 الرد: {value}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


def process_edit_value(message, key):
    if message.from_user.id != ADMIN_ID:
        return
    global responses
    value = message.text.strip()
    responses = load_responses()
    responses[key] = value
    save_responses(responses)
    bot.send_message(
        message.chat.id,
        f"✅ **تم تعديل الرد بنجاح!**\n\n🔑 الكلمة: `{key}`\n💬 الرد الجديد: {value}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# ----------------- الرد التلقائي في محادثات الأعمال -----------------

@bot.business_message_handler(func=lambda message: True)
def handle_business_message(business_message):
    try:
        global responses

        # مهم: تجاهل أي رسالة مبعوتة منك انت (صاحب الحساب) نفسك
        # عشان البوت ميردش عليك وانت بترد يدوي على العميل
        if business_message.from_user.id == ADMIN_ID:
            return

        responses = load_responses()
        user_text = business_message.text
        if not user_text:
            return

        clean_text = user_text.strip().lower()

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
    bot.remove_webhook()
    print("🚀 Coursatk Business Bot is online & running...")
    bot.infinity_polling()
