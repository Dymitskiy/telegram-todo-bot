import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client
from datetime import datetime, timedelta, timezone
import time
import threading
ADMIN_CHAT_ID = 566508867  # ← твій chat_id
TEXTS = {
    "welcome": {
        "uk": "Я телеграм бот 🤖 DYMYTSKIY ✅",
        "en": "I am a Telegram bot 🤖 DYMYTSKIY ✅"
    },
    "menu": {
        "uk": "Обери дію:",
        "en": "Choose an action:"
    },
    "choose_language": {
        "uk": "🌍 Обери мову",
        "en": "🌍 Choose language"
    },
    "language_changed": {
        "uk": "🌍 Мову змінено",
        "en": "🌍 Language changed"
    }
    }
TEXTS.update({
    "choose_category": {
        "uk": "📂 Обери категорію:",
        "en": "📂 Choose a category:"
    },
    "enter_task": {
        "uk": "✍️ Напиши задачу для категорії:",
        "en": "✍️ Enter task for category:"
    },
    "enter_delete_number": {
        "uk": "🗑 Введи номер задачі:",
        "en": "🗑 Enter task number:"
    },
    "task_added": {
        "uk": "✅ Задачу додано:",
        "en": "✅ Task added:"
    },
    "task_deleted": {
        "uk": "🗑 Задачу видалено",
        "en": "🗑 Task deleted"
    },
    "task_done": {
        "uk": "🎉 Задачу позначено як виконану",
        "en": "🎉 Task marked as done"
    },
    "done_button": {
        "uk": "✔ Виконано",
        "en": "✔ Done"
    },
    "remind_button": {
        "uk": "⏰ Нагадати",
        "en": "⏰ Remind"
    },
    "ask_remind_minutes": {
        "uk": "⏰ Через скільки хвилин нагадати?",
        "en": "⏰ Remind after how many minutes?"
    },
    "remind_set": {
        "uk": "⏰ Готово! Нагадаю через",
        "en": "⏰ Done! I will remind in"
    },
    "invalid_number": {
        "uk": "❌ Введи коректне число",
        "en": "❌ Enter a valid number"
    },
    "unknown_action": {
        "uk": "🤔 Обери дію з меню",
        "en": "🤔 Choose an action from the menu"
    },
    "back": {
        "uk": "↩ Назад",
        "en": "↩ Back"
    },
    "premium_info": {
        "uk": (
            "💎 Premium доступ:\n\n"
            "✅ Безліміт задач\n"
            "⏰ Безліміт нагадувань\n"
            "📂 Розширені фільтри\n"
            "🚀 Майбутні фічі\n\n"
            "👉 Натисни кнопку 💎 Premium"
        ),
        "en": (
            "💎 Premium access:\n\n"
            "✅ Unlimited tasks\n"
            "⏰ Unlimited reminders\n"
            "📂 Advanced filters\n"
            "🚀 Future features\n\n"
            "👉 Tap the 💎 Premium"
        )
    }
})
TEXTS["menu_buttons"] = {
    "active": {"uk": "🟡 Активні", "en": "🟡 Active"},
    "done": {"uk": "✅ Виконані", "en": "✅ Done"},
    "all": {"uk": "📋 Всі", "en": "📋 All"},
    "add": {"uk": "➕ Додати", "en": "➕ Add"},
    "delete": {"uk": "🗑 Видалити", "en": "🗑 Delete"},
    "premium": {"uk": "💎 Premium", "en": "💎 Premium"},
    "language": {"uk": "🌍", "en": "🌍"},
}
TEXTS["menu_title"] = {
    "uk": "👇 Меню",
    "en": "👇 Menu"
}
TEXTS["no_tasks"] = {
    "uk": "📭 У тебе немає задач",
    "en": "📭 No tasks yet"
}
TEXTS["premium_soon"] = {
    "uk": (
        "🔥 Чудово!\n\n"
        "Найближчим часом з Вами звʼяжеться адміністратор "
        "для активації Premium-статусу 💎"
    ),
    "en": (
        "🔥 Great!\n\n"
        "An admin will contact you shortly to activate your Premium status 💎"
    )
}
TEXTS["status_free"] = {
    "uk": (
        "📊 Твій статус:\n\n"
        "План: Free\n"
        "Задач: {tasks}/{limit}\n"
        "Повторювані задачі: ❌\n"
        "Нагадування на дату і час: ❌\n\n"
        "💎 Premium:\n"
        "• Безліміт задач\n"
        "• Повторювані задачі\n"
        "• Нагадування на дату і час\n\n"
        "👉 Напиши: ХОЧУ PREMIUM"
    ),
    "en": (
        "📊 Your status:\n\n"
        "Plan: Free\n"
        "Tasks: {tasks}/{limit}\n"
        "Recurring tasks: ❌\n"
        "Date & time reminders: ❌\n\n"
        "💎 Premium:\n"
        "• Unlimited tasks\n"
        "• Recurring tasks\n"
        "• Date & time reminders\n\n"
        "👉 Type: I WANT PREMIUM"
    )
}
TEXTS["status_premium"] = {
    "uk": (
        "📊 Твій статус:\n\n"
        "План: 💎 Premium\n"
        "Задач: {tasks} / ∞\n"
        "Повторювані задачі: ✅\n"
        "Нагадування на дату і час: ✅\n\n"
        "Дякуємо, що підтримуєш продукт ❤️"
    ),
    "en": (
        "📊 Your status:\n\n"
        "Plan: 💎 Premium\n"
        "Tasks: {tasks} / ∞\n"
        "Recurring tasks: ✅\n"
        "Date & time reminders: ✅\n\n"
        "Thank you for supporting the product ❤️"
    )
}
TEXTS["menu_buttons"]["status"] = {"uk": "📊 Статус", "en": "📊 Status"}

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

def t(lang, key):
    return TEXTS[key][lang]

def language_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    return kb

def add_task_db(chat_id, text, category, repeat_type="none"):
    next_run = calculate_next_run(repeat_type)

    supabase.table("tasks").insert({
        "chat_id": str(chat_id),
        "text": text,
        "category": category,
        "status": "active",
        "repeat_type": repeat_type,
        "next_run": next_run.isoformat() if next_run else None
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
    chat_id = str(chat_id)  # ← КЛЮЧОВО

    response = supabase.table("users") \
        .select("*") \
        .eq("chat_id", chat_id) \
        .execute()

    if response.data:
        return response.data[0]

    user = {
        "chat_id": chat_id,
        "language": None,
        "plan": "free"
    }

    supabase.table("users").insert(user).execute()
    return user

def send_language_menu(chat_id):
    lang = get_lang(chat_id)

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    bot.send_message(
        chat_id,
        t(lang, "choose_language"),
        reply_markup=keyboard
    )

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
        lang = get_lang(chat_id)
        bot.send_message(chat_id, t(lang, "no_tasks"))
        send_menu(chat_id)
        return

    lang = get_lang(chat_id)
    text = t(lang, "enter_delete_number") + "\n"

    for i, task in enumerate(tasks, start=1):
        text += f"{i}. [{task['category']}] {task['text']}\n"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(back_button(chat_id))

    bot.send_message(
        chat_id,
        text,
        reply_markup=keyboard
    )

def get_lang(chat_id):
    return (get_or_create_user(chat_id).get("language") or "uk")

def reminder_worker():
    while True:
        try:
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
        except Exception as e:
            print("REMINDER ERROR:", e)
        time.sleep(30)  # ← ОБОВʼЯЗКОВО ВСЕРЕДИНІ while

def build_status_text(chat_id):
    lang = get_lang(chat_id)
    plan = get_user_plan(chat_id)
    tasks_count = get_tasks_count(chat_id)

    if plan == "premium":
        return t(lang, "status_premium").format(tasks=tasks_count)
    else:
        return t(lang, "status_free").format(
            tasks=tasks_count,
            limit=FREE_LIMIT
        )

def show_filtered_tasks(chat_id, status):
    tasks = get_tasks_by_status(chat_id, status)

    if not tasks:
        lang = get_lang(chat_id)
        bot.send_message(chat_id, t(lang, "no_tasks"))
        send_menu(chat_id)
        return

    text = ""
    keyboard = InlineKeyboardMarkup()

    for task in tasks:
        icon = "✅" if task["status"] == "done" else "🟡"
        text += f"{icon} [{task['category']}] {task['text']}\n"

        if task["status"] == "active":
            lang = get_lang(chat_id)
            keyboard.add(
            InlineKeyboardButton(
                t(lang, "done_button"),
                callback_data=f"done_{task['id']}"
            ),
            InlineKeyboardButton(
                t(lang, "remind_button"),
                callback_data=f"remind_{task['id']}"
            ))
            
    bot.send_message(chat_id, text, reply_markup=keyboard)

def recurring_worker():
    while True:
        try:
            now = datetime.now(timezone.utc).isoformat()

            response = supabase.table("tasks") \
                .select("*") \
                .neq("repeat_type", "none") \
                .lte("next_run", now) \
                .execute()

            for task in response.data:
                next_run = calculate_next_run(task["repeat_type"])

                supabase.table("tasks").update({
                    "next_run": next_run.isoformat() if next_run else None,
                    "status": "active"
                }).eq("id", task["id"]).execute()

                bot.send_message(
                    int(task["chat_id"]),
                    f"🔁 Повторювана задача:\n[{task['category']}] {task['text']}"
                )

        except Exception as e:
            print("RECURRING ERROR:", e)

        time.sleep(60)
threading.Thread(target=recurring_worker, daemon=True).start()

def calculate_next_run(repeat_type):
    now = datetime.now(timezone.utc)

    if repeat_type == "daily":
        return now + timedelta(days=1)

    if repeat_type == "weekly":
        return now + timedelta(weeks=1)

    return None

STATE_WAITING_DELETE = "waiting_delete"
STATE_WAITING_REPEAT_TYPE = "waiting_repeat_type"
STATE_WAITING_REMIND_DATETIME = "waiting_remind_datetime"

def set_state(chat_id, state):
    user_states[chat_id] = {"state": state}

def send_menu(chat_id):
    lang = get_lang(chat_id)
    tbtn = TEXTS["menu_buttons"]

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(tbtn["active"][lang], callback_data="filter_active"),
        InlineKeyboardButton(tbtn["done"][lang], callback_data="filter_done"),
    )

    keyboard.add(
        InlineKeyboardButton(tbtn["all"][lang], callback_data="filter_all"),
    )

    keyboard.add(
        InlineKeyboardButton(tbtn["add"][lang], callback_data="add"),
        InlineKeyboardButton(tbtn["delete"][lang], callback_data="delete"),
    )

    plan = get_user_plan(chat_id)

    # 💎 Premium button — ТІЛЬКИ якщо НЕ premium
    if plan != "premium":
        keyboard.add(
            InlineKeyboardButton(tbtn["premium"][lang], callback_data="premium")
        )

    # 📊 Status button — ТІЛЬКИ якщо НЕ premiums
    if plan != "premium":
        keyboard.add(
            InlineKeyboardButton(tbtn["status"][lang], callback_data="status"),
            InlineKeyboardButton(tbtn["language"][lang], callback_data="change_language")
        )
    else:
        # для premium залишаємо тільки мову
        keyboard.add(
            InlineKeyboardButton(tbtn["language"][lang], callback_data="change_language")
        )
    lang = get_lang(chat_id)
    bot.send_message(chat_id, t(lang, "menu_title"), reply_markup=keyboard)

def back_button(chat_id):
    lang = get_lang(chat_id)
    return InlineKeyboardButton(t(lang, "back"), callback_data="back")

user_states = {}  # chat_id: state

def send_category_menu(chat_id):
    keyboard = InlineKeyboardMarkup()

    for cat in CATEGORIES[get_lang(chat_id)]:
        keyboard.add(
            InlineKeyboardButton(cat, callback_data=f"cat:{cat}")
        )

    keyboard.add(back_button(chat_id))   # ← ДОДАЛИ

    lang = get_lang(chat_id)
    bot.send_message(chat_id, t(lang, "choose_category"), reply_markup=keyboard)

CATEGORIES = {
    "uk": ["Робота", "Дім", "Терміново"],
    "en": ["Work", "Home", "Urgent"]
}

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    # 1️⃣ створюємо або знаходимо користувача
    user = get_or_create_user(chat_id)

    # 2️⃣ визначаємо мову (якщо ще не вибрана — uk)
    lang = user.get("language") or "uk"

    # 3️⃣ локалізоване привітання
    bot.send_message(
        chat_id,
        TEXTS["welcome"][lang]
    )

    # 4️⃣ якщо мова ще не вибрана — показуємо вибір
    if not user.get("language"):
        bot.send_message(
            chat_id,
            TEXTS["choose_language"]["uk"],
            reply_markup=language_keyboard()
        )
    else:
        send_menu(chat_id)

@bot.callback_query_handler(func=lambda c: c.data == "status")
def status_callback(c):
    chat_id = c.message.chat.id

    # очищаємо можливий state
    user_states.pop(chat_id, None)

    bot.send_message(
        chat_id,
        build_status_text(chat_id)
    )

@bot.message_handler(commands=["myid"])
def myid(message):
    bot.send_message(
        message.chat.id,
        f"Твій Telegram ID (chat_id): {message.chat.id}"
    )

@bot.callback_query_handler(func=lambda c: c.data == "change_language")
def change_language(c):
    chat_id = c.message.chat.id
    lang = get_lang(chat_id)

    bot.send_message(
        chat_id,
        t(lang, "choose_language"),
        reply_markup=language_keyboard()
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def set_language(c):
    chat_id = str(c.message.chat.id)
    lang = c.data.split("_")[1]  # uk або en

    # 1️⃣ зберігаємо мову в Supabase
    supabase.table("users") \
        .update({"language": lang}) \
        .eq("chat_id", chat_id) \
        .execute()

    # 2️⃣ ПОВТОРНО читаємо користувача з БД (КЛЮЧОВО!)
    user = get_or_create_user(chat_id)
    lang = user["language"]


    # 3️⃣ повідомлення + меню ВЖЕ НОВОЮ МОВОЮ
    bot.send_message(
        chat_id,
        TEXTS["language_changed"][lang]
    )
    send_menu(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
def callback_category(c):
    chat_id = c.message.chat.id
    category = c.data.split(":")[1]

    user_states[chat_id] = {
        "state": "waiting_task_text",
        "category": category,
        "repeat_type": "none"
    }

    keyboard = InlineKeyboardMarkup()
    keyboard.add(back_button(chat_id))

    lang = get_lang(chat_id)
    bot.send_message(
        chat_id,
        f"{t(lang, 'enter_task')} {category}",
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

@bot.callback_query_handler(func=lambda c: c.data == "premium")
def premium_callback(c):
    chat_id = c.message.chat.id
    lang = get_lang(chat_id)

    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            "✅ Я оплатив" if lang == "uk" else "✅ I’ve paid",
            callback_data="paid"
        )
    )

    bot.send_message(
        chat_id,
        t(lang, "premium_soon") + "\n\n"
        + ("Після оплати натисни кнопку нижче 👇"
           if lang == "uk"
           else "After the payment, tap the button below 👇"),
        reply_markup=keyboard
    )

    # 🔔 повідомлення адміну
    bot.send_message(
        ADMIN_CHAT_ID,
        f"💎 Запит на Premium\n\n"
        f"chat_id: {chat_id}\n"
        f"мова: {lang}\n"
        f"дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

@bot.callback_query_handler(func=lambda call: call.data == "delete")
def on_delete(call):
    set_state(call.message.chat.id, STATE_WAITING_DELETE)
    show_tasks_with_numbers(call.message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("done_"))
def mark_done(c):
    chat_id = c.message.chat.id
    task_id = c.data.split("_")[1]

    supabase.table("tasks")\
        .update({"status": "done"})\
        .eq("id", task_id)\
        .execute()

    bot.answer_callback_query(c.id, "Задача виконана ✅")
    lang = get_lang(chat_id)
    bot.send_message(chat_id, t(lang, "no_tasks"))
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
    chat_id = call.message.chat.id
    task_id = int(call.data.split("_")[1])

    user_states[chat_id] = {
        "state": STATE_WAITING_REMIND_DATETIME,
        "task_id": task_id
    }

    bot.send_message(
        chat_id,
        "🗓 Введи дату і час нагадування\n\n"
        "Формат:\n"
        "DD.MM.YYYY HH:MM\n\n"
        "Приклад:\n"
        "25.09.2026 19:00"
    )

@bot.callback_query_handler(func=lambda call: call.data == "back")
def callback_back(call):
    user_states.pop(call.message.chat.id, None)
    send_menu(call.message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("repeat:"))
def choose_repeat(c):
    chat_id = c.message.chat.id
    repeat_type = c.data.split(":")[1]

    state_data = user_states.get(chat_id)
    if not state_data or state_data.get("state") != STATE_WAITING_REPEAT_TYPE:
        bot.answer_callback_query(c.id)
        return

    category = state_data["category"]
    text = state_data["text"]

    plan = get_user_plan(chat_id)

    # 💎 Premium-перевірка
    if plan == "free" and repeat_type != "none":
        bot.send_message(
            chat_id,
            "🔒 Повторювані задачі доступні лише в Premium 💎\n\n"
            "✔ Безліміт задач\n"
            "✔ Повторювані задачі\n"
            "✔ Безліміт нагадувань\n\n"
            "👉 Напиши: ХОЧУ PREMIUM"
        )
        send_menu(chat_id)
        user_states.pop(chat_id, None)
        return

    # 🔒 Free-ліміт задач
    if plan == "free":
        count = get_tasks_count(chat_id)
        if count >= FREE_LIMIT:
            bot.send_message(
                chat_id,
                "🔒 Ліміт безкоштовного плану — 20 задач.\n\n"
                "💎 Оформи Premium"
            )
            send_menu(chat_id)
            user_states.pop(chat_id, None)
            return

    # ✅ ВСЕ ДОБРЕ — додаємо задачу
    add_task_db(chat_id, text, category, repeat_type)

    user_states.pop(chat_id, None)

    bot.send_message(
        chat_id,
        f"✅ Задачу додано:\n{text}\n📂 Категорія: {category}"
    )
    send_menu(chat_id)

@bot.message_handler(commands=["reply"])
def admin_reply(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return  # захист

    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        bot.send_message(
            message.chat.id,
            "❌ Формат:\n/reply chat_id текст повідомлення"
        )
        return

    target_chat_id = int(parts[1])
    text = parts[2]

    bot.send_message(target_chat_id, text)
    bot.send_message(
        message.chat.id,
        f"✅ Повідомлення надіслано користувачу {target_chat_id}"
    )

@bot.message_handler(commands=["grant_premium"])
def grant_premium(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Формат: /grant_premium chat_id")
        return

    target_chat_id = parts[1]

    supabase.table("users").update({
        "plan": "premium",
        "premium_activated_at": datetime.utcnow().isoformat()
    }).eq("chat_id", target_chat_id).execute()


    bot.send_message(
        target_chat_id,
        "🎉 Premium активовано!\n\nДякуємо за підтримку 💎"
    )

    send_menu(target_chat_id)

    bot.send_message(
        message.chat.id,
        f"✅ Premium видано користувачу {target_chat_id}"
    )

@bot.callback_query_handler(func=lambda c: c.data == "paid")
def paid_callback(c):
    chat_id = c.message.chat.id
    lang = get_lang(chat_id)

    bot.send_message(
        chat_id,
        "🙏 Дякую! Ми перевіримо оплату і активуємо Premium найближчим часом."
        if lang == "uk"
        else "🙏 Thank you! We’ll verify the payment and activate Premium shortly."
    )

    bot.send_message(
        ADMIN_CHAT_ID,
        f"💰 Користувач натиснув «Я оплатив»\n\n"
        f"chat_id: {chat_id}\n"
        f"дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

@bot.message_handler(commands=["admin_stats"])
def admin_stats(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    users = supabase.table("users").select(
        "plan, premium_activated_at"
    ).execute().data

    total = len(users)
    premium = sum(1 for u in users if u["plan"] == "premium")
    free = total - premium

    last_premium = None
    premium_dates = [
        u["premium_activated_at"]
        for u in users
        if u["premium_activated_at"]
    ]
    if premium_dates:
        last_premium = max(premium_dates)

    text = (
        "📊 Статистика бота\n\n"
        f"👥 Всього користувачів: {total}\n"
        f"💎 Premium: {premium}\n"
        f"🆓 Free: {free}\n"
    )

    if last_premium:
        text += f"\n📅 Остання активація:\n{last_premium}"

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    lang = get_lang(chat_id)

    state_data = user_states.get(chat_id)

    # ⏰ ВВЕДЕННЯ ДАТИ + ЧАСУ НАГАДУВАННЯ (ПЕРШЕ!)
    if isinstance(state_data, dict) and state_data.get("state") == STATE_WAITING_REMIND_DATETIME:
        try:
            remind_dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
            remind_dt = remind_dt.replace(tzinfo=timezone.utc)

            supabase.table("tasks").update({
                "remind_at": remind_dt.isoformat()
            }).eq("id", state_data["task_id"]).execute()

            user_states.pop(chat_id, None)

            bot.send_message(
                chat_id,
                f"⏰ Нагадування встановлено:\n"
                f"{remind_dt.strftime('%d.%m.%Y %H:%M')}"
            )
            send_menu(chat_id)

        except ValueError:
            bot.send_message(
                chat_id,
                "❌ Невірний формат.\n"
                "Спробуй так:\n"
                "25.09.2026 19:00"
            )

        return


    # ➕ Користувач вводить текст задачі
    if isinstance(state_data, dict) and state_data.get("state") == "waiting_task_text":
        category = state_data["category"]

        user_states[chat_id] = {
            "state": STATE_WAITING_REPEAT_TYPE,
            "category": category,
            "text": text
        }

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("❌ Без повторення", callback_data="repeat:none")
        )
        keyboard.add(
            InlineKeyboardButton("🔁 Щодня (Premium)", callback_data="repeat:daily"),
            InlineKeyboardButton("🔁 Щотижня (Premium)", callback_data="repeat:weekly")
        )

        bot.send_message(
            chat_id,
            "🔁 Повторювати задачу?",
            reply_markup=keyboard
        )
        return

    # 🗑 Видалення задачі
    if isinstance(state_data, dict) and state_data.get("state") == STATE_WAITING_DELETE:
        if not text.isdigit():
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, t(lang, "no_tasks"))
            return

        index = int(text) - 1
        tasks = get_tasks_db(chat_id)

        if index < 0 or index >= len(tasks):
            bot.send_message(chat_id, t(lang, "no_tasks"))
            return

        task_id = tasks[index]["id"]
        delete_task_db(task_id, chat_id)

        user_states.pop(chat_id, None)
        bot.send_message(chat_id, t(lang, "task_deleted"))
        send_menu(chat_id)
        return

    # ❓ Невідомий текст
    bot.send_message(chat_id, t(lang, "unknown_action"))
    send_menu(chat_id)

print("🤖 Бот запущено")
import sys
sys.stdout.flush()
threading.Thread(target=reminder_worker, daemon=True).start()
bot.infinity_polling()