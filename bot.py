import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не заданий")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Supabase credentials not set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

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
    print("TASKS FROM DB:", response.data)

    response = query.order("id").execute()
    return response.data

def show_tasks_with_numbers(chat_id):
    tasks = get_tasks_db(chat_id)

    if not tasks:
        bot.send_message(chat_id, "📭 У тебе немає задач")
        send_menu(chat_id)
        return

    text = "🗑 Введи номер задачі:\n"
    for i, task in enumerate(tasks, start=1):
        text += f"{i}. [{task['category']}] {task['text']}\n"

    bot.send_message(chat_id, text)

user_states = {}

STATE_WAITING_DELETE = "waiting_delete"

def set_state(chat_id, state):
    user_states[chat_id] = state
def send_menu(chat_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("➕ Додати", callback_data="add"),
        InlineKeyboardButton("🗑 Видалити", callback_data="delete"),
        InlineKeyboardButton("📋 Список", callback_data="list")
    )
    bot.send_message(chat_id, "Обери дію:", reply_markup=keyboard)

user_states = {}  # chat_id: state

def send_category_menu(chat_id):
    keyboard = InlineKeyboardMarkup()
    for cat in CATEGORIES:
        keyboard.add(
            InlineKeyboardButton(cat, callback_data=f"cat:{cat}")
        )
    bot.send_message(chat_id, "📂 Обери категорію:", reply_markup=keyboard)

CATEGORIES = ["Робота", "Дім", "Терміново"]

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Я телеграм бот🤖DYMYTSKIY ✅")
    send_menu(message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
def callback_category(c):
    chat_id = c.message.chat.id
    category = c.data.split(":")[1]

    user_states[chat_id] = {
        "state": "waiting_task_text",
        "category": category
    }

    bot.send_message(chat_id, f"✍️ Напиши задачу для категорії: {category}")

@bot.callback_query_handler(func=lambda c: c.data == "add")
def callback_add(c):
    send_category_menu(c.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "list")
def callback_list(call):
    if not tasks:
        bot.send_message(chat_id, "📭 Немає активних задач")
        send_menu(chat_id)
        return
    chat_id = call.message.chat.id
    tasks = get_tasks_db(call.message.chat.id)
    text = ""
    keyboard = InlineKeyboardMarkup()

    for task in tasks:
        status_icon = "✅" if task["status"] == "done" else "🟡"
        text += f"{status_icon} [{task['category']}] {task['text']}\n"

        if task["status"] == "active":
            keyboard.add(
                InlineKeyboardButton(
                    text="✔ Виконано",
                    callback_data=f"done_{task['id']}"
                )
            )

    bot.send_message(
        chat_id,
        text or "📭 Немає активних задач",
        reply_markup=keyboard
    )

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

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

    state_data = user_states.get(chat_id)

    # ➕ Додавання задачі
    if isinstance(state_data, dict) and state_data.get("state") == "waiting_task_text":
        category = state_data["category"]

        add_task_db(chat_id, text, category)

        user_states.pop(chat_id, None)

        bot.send_message(
            chat_id,
            f"✅ Задачу додано:\n{text}\n📂 Категорія: {category}"
        )
        send_menu(chat_id)
        return

    # 🗑 Видалення задачі
    if user_states.get(chat_id) == STATE_WAITING_DELETE:
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
bot.infinity_polling()





