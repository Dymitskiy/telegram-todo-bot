import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
TOKEN = "8408192846:AAGK1EQ435si0EMD4PO0KO_1n-SrhBvfX1U"
bot = telebot.TeleBot(TOKEN)
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
def get_tasks_text():
    if not tasks:
        return "📭 Список задач порожній"

    result = "📋 Твої задачі:\n"
    for i, task in enumerate(tasks, start=1):
        result += f"{i}. {task}\n"

    return result
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

def is_waiting_task(chat_id):
    return user_states.get(chat_id) == "waiting_task"
def send_menu(chat_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("➕ Додати", callback_data="add"),
        InlineKeyboardButton("🗑 Видалити", callback_data="delete"),
        InlineKeyboardButton("📋 Список", callback_data="list")
    )
    bot.send_message(chat_id, "Обери дію:", reply_markup=keyboard)
import json
import os
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
user_states = {}
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привіт! Я телеграм бот🤖DYMITSKIY чим можу допомогти? "
    )
    send_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "add")
def on_add(call):
    set_state(call.message.chat.id, STATE_WAITING_TASK)
    bot.send_message(call.message.chat.id, "✍️ Напиши текст задачі:")

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
    text = message.text.strip()
    state = user_states.get(chat_id)

    if state == STATE_WAITING_TASK:
        add_task(chat_id, text)
        bot.send_message(chat_id, "✅ Додано")
        send_menu(chat_id)

    elif state == STATE_WAITING_DELETE:
        if not text.isdigit():
            bot.send_message(chat_id, "❌ Введи номер")
            return
        deleted = delete_task(chat_id, int(text)-1)
        bot.send_message(chat_id, f"🗑 Видалено: {deleted}")
        send_menu(chat_id)

    else:
        send_menu(chat_id)


print("Бот запущено...")
bot.infinity_polling()


