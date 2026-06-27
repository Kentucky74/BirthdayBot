import os
import datetime
import sqlite3

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8780127018:AAFaX48_joQwXUI0I8EwOOfIHkZWElNAOVM"

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


# --- HELPERS ---
def add_birthday_db(user_id, name, day, month):
    cur.execute(
        "INSERT INTO birthdays VALUES (?, ?, ?, ?)",
        (user_id, name, day, month)
    )
    conn.commit()


def get_birthdays(user_id):
    cur.execute("SELECT name, day, month FROM birthdays WHERE user_id=?",
                (user_id,))
    return cur.fetchall()


# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.send_message(
        "🎂 Бот дней рождений\n\n"
        "/add Имя ДД.ММ\n"
        "/list\n"
        "/test"
    )

async def delete_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Использование: /delete Имя"
        )

        return

    name = " ".join(context.args)

    cur.execute(
        "DELETE FROM birthdays WHERE user_id=? AND name=?",
        (user_id, name)
    )
    conn.commit()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🗑 Удалено: {name}"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.args[0]
        date = context.args[1]

        day, month = map(int, date.split("."))

        add_birthday_db(update.effective_user.id, name, day, month)

        await update.message.send_message("✅ Добавлено!")

    except:
        await update.message.send_message("❌ Используй: /add Имя ДД.ММ")


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_birthdays(update.effective_user.id)

    if not data:
        await update.message.send_message("Список пуст")
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

    await update.message.send_message(text)


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.send_message("🧪 Бот работает! Test OK ✅")
async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):

    today = datetime.date.today()

    cur.execute("SELECT user_id, name, day, month FROM birthdays")
    rows = cur.fetchall()

    for user_id, name, day, month in rows:

        if day == today.day and month == today.month:

            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Сегодня день рождения у {name}!\n🎁 Поздравляем! 🥳"
            )

# --- MAIN ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("test", test))
    
    job_queue = app.job_queue
    job_queue.run_daily(
        check_birthdays,
        time=datetime.time(23,34)
    )

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):

    today = datetime.date.today()

    cur.execute("SELECT user_id, name, day, month FROM birthdays")
    rows = cur.fetchall()

    for user_id, name, day, month in rows:

        if day == today.day and month == today.month:

            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Сегодня день рождения у {name}!\n🎁 Поздравляем с днем рождения! Желаю здоровья и всех благ 🥳"
            )
async def delete_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Использование: /delete Имя"
        )
        return

    name = " ".join(context.args)

    cur.execute(
        "DELETE FROM birthdays WHERE user_id=? AND name=?",
        (user_id, name)
    )
    conn.commit()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🗑️ Удалено: {name}"
    )