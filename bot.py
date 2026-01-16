import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не заданий")

bot = telebot.TeleBot(TOKEN)

tasks = {}  
# формат:
# {
#   chat_id: ["задача 1", "задача 2"]
# }
user_states = {}

def add_task(chat_id, text):
    chat_id = str(chat_id)
    tasks.setdefault(chat_id, []).append(text)
    save_tasks(tasks)
    user_states.pop(chat_id, None)
def delete_task(chat_id, index):
    chat_id = str(chat_id)
    deleted = tasks[chat_id].pop(index)
    save_tasks(tasks)
    user_states.pop(chat_id, None)
    return deleted
def show_tasks_with_numbers(chat_id):
    chat_id = str(chat_id)
    user_tasks = tasks.get(chat_id, [])

    if not user_tasks:
        bot.send_message(chat_id, "📭 У тебе немає задач")
        send_menu(chat_id)
        return

    text = "🗑 Введи номер задачі:\n"
    for i, task in enumerate(user_tasks, start=1):
        text += f"{i}. {task}\n"

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
import json
TASKS_FILE = "tasks.json"
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}

    with open(TASKS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)
def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as file:
        json.dump(tasks, file, ensure_ascii=False, indent=2)

tasks = load_tasks()
user_states = {}  # chat_id: state

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привіт! Я телеграм бот🤖DYMITSKIY чим можу допомогти? "
    )
    send_menu(message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data == "add")
def callback_add(c):
    chat_id = c.message.chat.id
    set_state(chat_id, STATE_WAITING_TASK)
    bot.send_message(chat_id, "✍️ Напиши текст задачі")

@bot.callback_query_handler(func=lambda call: call.data == "list")
def callback_list(call):
    chat_id = str(call.message.chat.id)

    user_tasks = tasks.get(chat_id, [])

    if not user_tasks:
        bot.send_message(chat_id, "📭 У тебе ще немає задач")
    else:
        text = "\n".join(f"{i+1}. {task}" for i, task in enumerate(user_tasks))
        bot.send_message(chat_id, text)

@bot.callback_query_handler(func=lambda call: call.data == "delete")
def on_delete(call):
    set_state(call.message.chat.id, STATE_WAITING_DELETE)
    show_tasks_with_numbers(call.message.chat.id)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

    if user_states.get(chat_id) == "waiting_task":
        chat_id_str = str(chat_id)
        tasks.setdefault(chat_id_str, []).append(text)
        save_tasks(tasks)
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, f"✅ Задачу додано:\n{text}")
        send_menu(chat_id)
    elif user_states.get(chat_id) == STATE_WAITING_DELETE:
        if not text.isdigit():
            bot.send_message(chat_id, "❌ Введи номер задачі")
            return

        index = int(text) - 1
        chat_id_str = str(chat_id)

        if index < 0 or index >= len(tasks.get(chat_id_str, [])):
            bot.send_message(chat_id, "❌ Невірний номер")
            return

        deleted = delete_task(chat_id, index)
        bot.send_message(chat_id, f"🗑 Видалено: {deleted}")
        send_menu(chat_id)
    else:
        bot.send_message(chat_id, "🤔 Обери дію з меню")
        send_menu(chat_id)


print("🤖 Бот запущено")

bot.infinity_polling(
    timeout=10,
    long_polling_timeout=5
)




