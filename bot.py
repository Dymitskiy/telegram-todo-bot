import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client
from datetime import datetime, timedelta, timezone
import time
import threading

TEXTS = {
    "start": {
        "ua": "Я телеграм бот 🤖 DYMYTSKIY ✅",
        "en": "I am a Telegram bot 🤖 DYMYTSKIY ✅"
    },
    "menu": {
        "ua": "Обери дію:",
        "en": "Choose an action:"
    },
    "choose_language": {
        "ua": "🌍 Обери мову",
        "en": "🌍 Choose language"
    }
}

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
FREE_LIMIT = 20
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не заданий")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Supabase credentials not set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

def t(chat_id, key):
    user = get_or_create_user(chat_id)
    lang = user.get("language", "ua")
    return TEXTS[key][lang]

def language_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    return kb

def add_task_db(chat_id, text, category):
    supabase.table("tasks").insert({
        "chat_id": str(chat_id),
        "text": text,
        "category": category,
        "status": "active"
    }).execute()

def delete_task_db(task_id, chat_id):
    supabase.table("tasks") \
        .delete() \
        .eq("id", task_id) \
        .eq("chat_id", str(chat_id)) \
        .execute()

def get_tasks_db(chat_id, only_active=True):
    query = supabase.table("tasks") \
        .select("*") \
        .eq("chat_id", str(chat_id))

    if only_active:
        query = query.eq("status", "active")

    response = query.order("id").execute()
    return response.data

def get_or_create_user(chat_id):
    response = supabase.table("users") \
        .select("*") \
        .eq("chat_id", chat_id) \
        .execute()

    if response.data:
        return response.data[0]

    user = {
        "chat_id": chat_id,
        "language": "ua",
        "plan": "free"
    }

    supabase.table("users").insert(user).execute()
    return user

def set_user_language(chat_id, language):
    supabase.table("users") \
        .update({"language": language}) \
        .eq("chat_id", chat_id) \
        .execute()

def get_tasks_count(chat_id):
    response = supabase.table("tasks") \
        .select("id", count="exact") \
        .eq("chat_id", str(chat_id)) \
        .execute()

    return response.count or 0

def get_user_plan(chat_id):
    response = supabase.table("users") \
        .select("plan") \
        .eq("chat_id", str(chat_id)) \
        .execute()

    if response.data:
        return response.data[0]["plan"]

    # якщо користувача ще немає — створюємо
    supabase.table("users").insert({
        "chat_id": str(chat_id),
        "plan": "free"
    }).execute()

    return "free"

def get_tasks_by_status(chat_id, status=None):
    query = supabase.table("tasks").select("*").eq("chat_id", str(chat_id))

    if status:
        query = query.eq("status", status)

    response = query.order("created_at").execute()
    return response.data or []

def show_tasks_with_numbers(chat_id):
    tasks = get_tasks_db(chat_id)

    if not tasks:
        bot.send_message(chat_id, "📭 У тебе немає задач")
        send_menu(chat_id)
        return

    text = "🗑 Введи номер задачі:\n"
    for i, task in enumerate(tasks, start=1):
        text += f"{i}. [{task['category']}] {task['text']}\n"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(back_button())

    bot.send_message(
        chat_id,
        text,
        reply_markup=keyboard
    )

def reminder_worker():
    while True:
        now = datetime.now(timezone.utc) .isoformat()
        response = supabase.table("tasks") \
            .select("*") \
            .not_.is_("remind_at", None) \
            .lte("remind_at", now) \
            .execute()


        for task in response.data:
            bot.send_message(
                int(task["chat_id"]),
                f"⏰ Нагадування:\n[{task['category']}] {task['text']}"
            )

            supabase.table("tasks").update({
                "remind_at": None
            }).eq("id", task["id"]).execute()

        time.sleep(30)  # ← ОБОВʼЯЗКОВО ВСЕРЕДИНІ while
 
user_states = {}

STATE_WAITING_DELETE = "waiting_delete"
STATE_WAITING_REMIND_TIME = "waiting_remind_time"

def set_state(chat_id, state):
    user_states[chat_id] = state
def send_menu(chat_id):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton("🟡 Активні", callback_data="filter_active"),
        InlineKeyboardButton("✅ Виконані", callback_data="filter_done"),
    )

    keyboard.add(
        InlineKeyboardButton("📋 Всі", callback_data="filter_all"),
    )

    keyboard.add(
        InlineKeyboardButton("➕ Додати", callback_data="add"),
        InlineKeyboardButton("🗑 Видалити", callback_data="delete"),
    )
    keyboard.add(
    InlineKeyboardButton("💎 Premium", callback_data="premium")
    )
    bot.send_message(chat_id, "👇 Меню", reply_markup=keyboard)
def back_button():
    return InlineKeyboardButton("↩ Назад", callback_data="back")

user_states = {}  # chat_id: state

def send_category_menu(chat_id):
    keyboard = InlineKeyboardMarkup()

    for cat in CATEGORIES:
        keyboard.add(
            InlineKeyboardButton(cat, callback_data=f"cat:{cat}")
        )

    keyboard.add(back_button())  # ← ДОДАЛИ

    bot.send_message(
        chat_id,
        "📂 Обери категорію:",
        reply_markup=keyboard
    )

CATEGORIES = ["Робота", "Дім", "Терміново"]

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    # 1️⃣ створюємо або знаходимо користувача
    user = get_or_create_user(chat_id)

    # 2️⃣ визначаємо мову (якщо ще не вибрана — ua)
    lang = user.get("language") or "ua"

    # 3️⃣ локалізоване привітання
    bot.send_message(
        chat_id,
        TEXTS["welcome"][lang]
    )

    # 4️⃣ якщо мова ще не вибрана — показуємо вибір
    if not user.get("language"):
        bot.send_message(
            chat_id,
            TEXTS["choose_language"]["ua"],
            reply_markup=language_keyboard()
        )
    else:
        send_menu(chat_id)

def show_filtered_tasks(chat_id, status):
    tasks = get_tasks_by_status(chat_id, status)

    if not tasks:
        bot.send_message(chat_id, "📭 Немає задач")
        send_menu(chat_id)
        return

    text = ""
    keyboard = InlineKeyboardMarkup()

    for task in tasks:
        icon = "✅" if task["status"] == "done" else "🟡"
        text += f"{icon} [{task['category']}] {task['text']}\n"

        if task["status"] == "active":
            keyboard.add(
                InlineKeyboardButton(
                    "✔ Виконано",
                    callback_data=f"done_{task['id']}"
                ),
                InlineKeyboardButton(
                    "⏰ Нагадати",
                    callback_data=f"remind_{task['id']}"
                )
            )
   
    bot.send_message(chat_id, text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def set_language(c):
    lang = c.data.split("_")[1]
    set_user_language(c.message.chat.id, lang)
    bot.send_message(c.message.chat.id, t(c.message.chat.id, "start"))
    send_menu(c.message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
def callback_category(c):
    chat_id = c.message.chat.id
    category = c.data.split(":")[1]

    user_states[chat_id] = {
        "state": "waiting_task_text",
        "category": category
    }

    keyboard = InlineKeyboardMarkup()
    keyboard.add(back_button())

    bot.send_message(
        chat_id,
        f"✍️ Напиши задачу для категорії: {category}",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda c: c.data == "add")
def callback_add(c):
    send_category_menu(c.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "list")
def callback_list(call):
    chat_id = call.message.chat.id

    tasks = get_tasks_db(chat_id)  # ← СПОЧАТКУ отримуємо задачі

    if not tasks:
        bot.send_message(chat_id, "📭 Немає активних задач")
        send_menu(chat_id)
        return

    text = ""
    keyboard = InlineKeyboardMarkup()

    for task in tasks:
        status = task["status"] or "active"
        status_icon = "✅" if status == "done" else "🟡"

        text += f"{status_icon} [{task['category']}] {task['text']}\n"

        if status == "active":
            keyboard.add(
                InlineKeyboardButton(
                    text="✔ Виконано",
                    callback_data=f"done_{task['id']}"
                )
            )

    bot.send_message(chat_id, text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "delete")
def on_delete(call):
    set_state(call.message.chat.id, STATE_WAITING_DELETE)
    show_tasks_with_numbers(call.message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("done_"))
def mark_done(c):
    task_id = c.data.split("_")[1]

    supabase.table("tasks")\
        .update({"status": "done"})\
        .eq("id", task_id)\
        .execute()

    bot.answer_callback_query(c.id, "Задача виконана ✅")
    bot.send_message(c.message.chat.id, "🎉 Задачу позначено як виконану")
    callback_list(c)        

@bot.callback_query_handler(func=lambda c: c.data == "filter_active")
def filter_active(call):
    show_filtered_tasks(call.message.chat.id, "active")

@bot.callback_query_handler(func=lambda c: c.data == "filter_done")
def filter_done(call):
    show_filtered_tasks(call.message.chat.id, "done")

@bot.callback_query_handler(func=lambda c: c.data == "filter_all")
def filter_all(call):
    show_filtered_tasks(call.message.chat.id, None)

@bot.callback_query_handler(func=lambda c: c.data.startswith("remind_"))
def remind_callback(call):
    task_id = int(call.data.split("_")[1])
    user_states[call.message.chat.id] = {
        "state": STATE_WAITING_REMIND_TIME,
        "task_id": task_id
    }
    keyboard = InlineKeyboardMarkup()
    keyboard.add(back_button())

    bot.send_message(
        call.message.chat.id,
        "⏰ Через скільки хвилин нагадати?",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "back")
def callback_back(call):
    user_states.pop(call.message.chat.id, None)
    send_menu(call.message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data == "premium")
def premium_info(c):
    bot.send_message(
        c.message.chat.id,
        "💎 Premium доступ:\n\n"
        "✅ Безліміт задач\n"
        "⏰ Безліміт нагадувань\n"
        "📂 Розширені фільтри\n"
        "🚀 Майбутні фічі\n\n"
        "Напиши:\n👉 ХОЧУ PREMIUM"
    )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    if text.lower() == "хочу premium":
        bot.send_message(
            chat_id,
            "🔥 Чудово!\n\n"
            "Premium буде доступний найближчим часом.\n"
            "Я повідомлю тебе першим 👌"
        )
        return
    
    state_data = user_states.get(chat_id)
    
    
    if isinstance(state_data, dict) and state_data.get("state") == STATE_WAITING_REMIND_TIME:
        if not text.isdigit() or int(text) <= 0:
            bot.send_message(chat_id, "❌ Введи число більше 0")
            return

        minutes = int(text)
        remind_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        supabase.table("tasks").update({
            "remind_at": remind_time.isoformat()
        }).eq("id", state_data["task_id"]).execute()

        user_states.pop(chat_id, None)
        bot.send_message(
            chat_id,
            f"⏰ Готово!\nНагадаю через {minutes} хвилин 📅"
        )
        send_menu(chat_id)
        return
    
    # ➕ Додавання задачі
    if isinstance(state_data, dict) and state_data.get("state") == "waiting_task_text":
        category = state_data["category"]

        plan = get_user_plan(chat_id)

        if plan == "free":
            count = get_tasks_count(chat_id)
            if count >= FREE_LIMIT:
                bot.send_message(
                    chat_id,
                    "🔒 Ліміт безкоштовного плану (20 задач).\n\n💎 Оформи Premium"
                )
                send_menu(chat_id)
                return

        add_task_db(chat_id, text, category)


        user_states.pop(chat_id, None)

        bot.send_message(
            chat_id,
            f"✅ Задачу додано:\n{text}\n📂 Категорія: {category}"
        )
        send_menu(chat_id)
        return

    # 🗑 Видалення задачі
    if isinstance(state_data, dict) and state_data.get("state") == STATE_WAITING_DELETE:
        if not text.isdigit():
            bot.send_message(chat_id, "❌ Введи номер задачі")
            return

        index = int(text) - 1
        tasks = get_tasks_db(chat_id)

        if index < 0 or index >= len(tasks):
            bot.send_message(chat_id, "❌ Невірний номер")
            return

        task_id = tasks[index]["id"]
        delete_task_db(task_id, chat_id)

        bot.send_message(chat_id, "🗑 Задачу видалено")
        user_states.pop(chat_id, None)
        send_menu(chat_id)
        return

    # ❓ Невідомий текст
    bot.send_message(chat_id, "🤔 Обери дію з меню")
    send_menu(chat_id)

print("🤖 Бот запущено")
import sys
sys.stdout.flush()
threading.Thread(target=reminder_worker, daemon=True).start()
bot.infinity_polling()




