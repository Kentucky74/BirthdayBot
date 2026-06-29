import datetime
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

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


# --- DB ---
def add_birthday(user_id, name, day, month):
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


def delete_birthday_db(user_id, name):
    cur.execute(
        "DELETE FROM birthdays WHERE user_id=? AND name=?",
        (user_id, name)
    )
    conn.commit()


# ---------------- MENU ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📋 Список", callback_data="list")],
    ]

    await update.message.reply_text(
        "🎂 Главное меню",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- CALLBACK ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "add":
        context.user_data["state"] = "add_name"
        await query.message.reply_text("Введите имя:")

    elif data == "list":
        data = get_birthdays(query.from_user.id)

        if not data:
            await query.message.reply_text("📭 Пусто")
            return

        text = "🎂 Список:\n\n"

        for name, day, month in data:
            text += f"{name} — {day:02}.{month:02}\n"

        await query.message.reply_text(text)


# ---------------- TEXT FLOW ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    state = context.user_data.get("state")

    # STEP 1: name
    if state == "add_name":
        context.user_data["name"] = update.message.text
        context.user_data["state"] = "add_date"
        await update.message.reply_text("Введите дату ДД.ММ")
        return

    # STEP 2: date
    if state == "add_date":
        try:
            day, month = map(int, update.message.text.split("."))

            name = context.user_data["name"]

            add_birthday(update.effective_user.id, name, day, month)

            context.user_data.clear()

            await update.message.reply_text("✅ Добавлено!")

        except:
            await update.message.reply_text("❌ Формат: ДД.ММ")

        return


# ---------------- AUTO CHECK ----------------
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


# ---------------- MAIN ----------------
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.job_queue.run_daily(
        check_birthdays,
        time=datetime.time(10, 0)  # время поздравления
    )

    print("BOT RUNNING")
    app.run_polling()


if __name__ == "__main__":
    main()