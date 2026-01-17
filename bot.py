from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import telebot

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Supabase credentials not set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_KEY exists:", bool(os.getenv("SUPABASE_KEY")))

def add_task_db(chat_id, text, category="general"):
    supabase.table("tasks").insert({
        "chat_id": str(chat_id),
        "text": text,
        "category": category
    }).execute()


def get_tasks_db(chat_id):
    response = supabase.table("tasks") \
        .select("*") \
        .eq("chat_id", str(chat_id)) \
        .order("id") \
        .execute()
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

def delete_task_db(task_id):
    supabase.table("tasks") \
        .delete() \
        .eq("id", task_id) \
        .execute()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не заданий")

bot = telebot.TeleBot(BOT_TOKEN)

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
    bot.send_message(message.chat.id, "Я телеграм бот🤖DYMITSKIY ✅")
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
    chat_id = call.message.chat.id
    tasks = get_tasks_db(chat_id)

    if not tasks:
        bot.send_message(chat_id, "📭 У тебе ще немає задач")
        return

    text = ""
    for i, task in enumerate(tasks, start=1):
        text += f"{i}. [{task['category']}] {task['text']}\n"

    bot.send_message(chat_id, text)

@bot.callback_query_handler(func=lambda call: call.data == "delete")
def on_delete(call):
    set_state(call.message.chat.id, STATE_WAITING_DELETE)
    show_tasks_with_numbers(call.message.chat.id)

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
        delete_task_db(task_id)

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





