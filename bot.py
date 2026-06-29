import datetime
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = "ТВОЙ_ТОКЕН_СЮДА"

# --- DB ---
conn = sqlite3.connect("birthdays.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS birthdays (
    user_id INTEGER,
    name TEXT,
    day INTEGER,
    month INTEGER
)
""")
conn.commit()


# --- DB FUNCTIONS ---
def add_birthday_db(user_id, name, day, month):
    cur.execute(
        "INSERT INTO birthdays VALUES (?, ?, ?, ?)",
        (user_id, name, day, month)
    )
    conn.commit()


def get_birthdays(user_id):
    cur.execute(
        "SELECT name, day, month FROM birthdays WHERE user_id=?",
        (user_id,)
    )
    return cur.fetchall()


# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📋 Список", callback_data="list")],
        [InlineKeyboardButton("🗑 Удалить", callback_data="delete")],
        [InlineKeyboardButton("🧪 Тест", callback_data="test")]
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🎂 Меню бота:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        name = context.args[0]
        date = context.args[1]

        day, month = map(int, date.split("."))

        add_birthday_db(update.effective_user.id, name, day, month)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ Добавлено!"
        )

    except:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Используй: /add Имя ДД.ММ"
        )


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = get_birthdays(update.effective_user.id)

    if not data:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📭 Список пуст"
        )
        return

    text = "🎂 Твои дни рождения:\n\n"
    today = datetime.date.today()

    for name, day, month in data:

        birthday = datetime.date(today.year, month, day)

        delta = (birthday - today).days

        if delta < 0:
            birthday = datetime.date(today.year + 1, month, day)
            delta = (birthday - today).days

        text += f"{name} — {day:02}.{month:02} (через {delta} дней)\n"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text
    )


async def delete_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Используй: /delete Имя"
        )
        return

    name = " ".join(context.args)

    cur.execute(
        "DELETE FROM birthdays WHERE user_id=? AND name=?",
        (update.effective_user.id, name)
    )
    conn.commit()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🗑 Удалено: {name}"
    )


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🧪 Бот работает!"
    )


# --- CALLBACK BUTTONS ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "add":
        await query.message.reply_text("Напиши:\n/add Имя ДД.ММ")

    elif data == "list":
        data = get_birthdays(query.from_user.id)

        if not data:
            await query.message.reply_text("📭 Список пуст")
            return

        text = "🎂 Список:\n\n"
        today = datetime.date.today()

        for name, day, month in data:

            birthday = datetime.date(today.year, month, day)
            delta = (birthday - today).days

            if delta < 0:
                birthday = datetime.date(today.year + 1, month, day)
                delta = (birthday - today).days

            text += f"{name} — {day:02}.{month:02} ({delta} дней)\n"

        await query.message.reply_text(text)

    elif data == "delete":
        await query.message.reply_text("Напиши:\n/delete Имя")

    elif data == "test":
        await query.message.reply_text("🧪 Бот работает!")


# --- AUTO BIRTHDAYS ---
async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):

    today = datetime.date.today()

    cur.execute("SELECT user_id, name, day, month FROM birthdays")
    rows = cur.fetchall()

    for user_id, name, day, month in rows:

        if day == today.day and month == today.month:

            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Сегодня день рождения у {name}! 🥳"
            )


# --- MAIN ---
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("delete", delete_birthday))
    app.add_handler(CommandHandler("test", test))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.job_queue.run_daily(
        check_birthdays,
        datetime.time(23, 34)
    )

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()