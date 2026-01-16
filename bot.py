from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import telebot
import sqlite3
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не заданий")

bot = telebot.TeleBot(BOT_TOKEN)

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    text TEXT,
    category TEXT
)
""")
conn.commit()

user_states = {}

def delete_task(chat_id, index):
    cursor.execute(
        "SELECT id, text FROM tasks WHERE chat_id = ?",
        (str(chat_id),)
    )
    rows = cursor.fetchall()

    task_id, task_text = rows[index]

    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )
    conn.commit()

    return task_text

def show_tasks_with_numbers(chat_id):
    cursor.execute(
        "SELECT text, category FROM tasks WHERE chat_id = ?",
        (str(chat_id),)
    )
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(chat_id, "📭 У тебе немає задач")
        return

    text = "🗑 Введи номер задачі:\n"
    for i, (task_text, category) in enumerate(rows, start=1):
        text += f"{i}. [{category}] {task_text}\n"

    bot.send_message(chat_id, text)

STATE_WAITING_TASK = "waiting_task"
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
    chat_id = c.message.chat.id
    set_state(chat_id, "waiting_category")
    send_category_menu(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "list")
def callback_list(call):
    chat_id = str(call.message.chat.id)

    cursor.execute(
    "SELECT text, category FROM tasks WHERE chat_id = ?",
    (chat_id,)
    )
    user_tasks = cursor.fetchall()


    if not user_tasks:
        bot.send_message(chat_id, "📭 У тебе ще немає задач")
    else:
        text = ""
        for i, task in enumerate(user_tasks, start=1):
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

    if isinstance(state_data, dict) and state_data.get("state") == "waiting_task_text":
        category = state_data["category"]

        task = {
            "text": message.text,
            "category": category
        }

        cursor.execute(
            "INSERT INTO tasks (chat_id, text, category) VALUES (?, ?, ?)",
            (str(chat_id), task["text"], task["category"])
        )
        conn.commit()

        user_states.pop(chat_id, None)

        bot.send_message(
            chat_id,
            f"✅ Задачу додано:\n{task['text']}\n📂 Категорія: {category}"
        )
        send_menu(chat_id)
    
    elif user_states.get(chat_id) == STATE_WAITING_DELETE:
        if not text.isdigit():
            bot.send_message(chat_id, "❌ Введи номер задачі")
            return

        index = int(text) - 1
        chat_id_str = str(chat_id)

        cursor.execute(
            "SELECT COUNT(*) FROM tasks WHERE chat_id = ?",
            (chat_id_str,)
        )
        count = cursor.fetchone()[0]

        if index < 0 or index >= count:
            bot.send_message(chat_id, "❌ Невірний номер")
            return
        deleted = delete_task(chat_id, index)
        bot.send_message(chat_id, f"🗑 Видалено: {deleted}")
        send_menu(chat_id)
    else:
        bot.send_message(chat_id, "🤔 Обери дію з меню")
        send_menu(chat_id)

print("🤖 Бот запущено")
import sys
sys.stdout.flush()
bot.infinity_polling()




