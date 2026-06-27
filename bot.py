import sqlite3
import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)


TOKEN = "8780127018:AAFaX48_joQwXUI0I8EwOOfIHkZWElNAOVM"

DB = "birthdays.db"


# ---------- База ----------

def connect():
    return sqlite3.connect(DB)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS birthdays(
        user_id INTEGER,
        name TEXT,
        day INTEGER,
        month INTEGER
    )
    """)

    conn.commit()
    conn.close()



def add_birthday(user_id, name, day, month):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO birthdays VALUES(?,?,?,?)",
        (user_id, name, day, month)
    )

    conn.commit()
    conn.close()



def get_birthdays(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT name, day, month FROM birthdays WHERE user_id=?",
        (user_id,)
    )

    data = cur.fetchall()

    conn.close()

    return data



def remove_birthday(user_id, name):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM birthdays WHERE user_id=? AND name=?",
        (user_id, name)
    )

    conn.commit()
    conn.close()



# ---------- Дни ----------


def days_left(day, month):

    today = datetime.date.today()

    birthday = datetime.date(
        today.year,
        month,
        day
    )

    if birthday < today:
        birthday = datetime.date(
            today.year + 1,
            month,
            day
        )

    return (birthday - today).days



# ---------- Команды ----------


async def start(update: Update, context):

    await update.message.reply_text(
        "🎂 Бот дней рождения\n\n"
        "Команды:\n\n"
        "/add Имя ДД.ММ\n"
        "/list\n"
        "/delete Имя"
    )



async def add(update: Update, context):

    if len(context.args) != 2:
        await update.message.reply_text(
            "Пример:\n/add Мама 15.08"
        )
        return


    name = context.args[0]
    date = context.args[1]

    try:

        day, month = map(int, date.split("."))

        add_birthday(
            update.effective_user.id,
            name,
            day,
            month
        )

        await update.message.reply_text(
            f"Добавлено 🎉\n{name} {date}"
        )


    except:

        await update.message.reply_text(
            "Ошибка даты"
        )




async def show(update: Update, context):

    data = get_birthdays(
        update.effective_user.id
    )


    if not data:

        await update.message.reply_text(
            "Список пуст"
        )
        return


    text = "🎂 Дни рождения:\n\n"


    for name, day, month in data:

        text += (
            f"{name}\n"
            f"{day:02}.{month:02}\n"
            f"Осталось: {days_left(day, month)} дней\n\n"
        )


    await update.message.reply_text(text)




async def delete(update: Update, context):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Пример:\n/delete Мама"
        )
        return


    name = context.args[0]

    remove_birthday(
        update.effective_user.id,
        name
    )

    await update.message.reply_text(
        "Удалено"
    )



# ---------- Ежедневная рассылка ----------


async def daily(context):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT DISTINCT user_id FROM birthdays"
    )

    users = cur.fetchall()

    conn.close()


    today = datetime.date.today()


    for user in users:

        user_id = user[0]

        data = get_birthdays(user_id)

        text = "🎂 Дни рождения:\n\n"


        for name, day, month in data:

            # если сегодня день рождения
            if today.day == day and today.month == month:

                text += (
                    f"🎉 Сегодня день рождения у {name}!\n"
                    f"🎁 Поздравляем! Желаем всех благ и крепкого здоровья 🥳\n\n"
                )

            else:

                text += (
                    f"{name} — через "
                    f"{days_left(day, month)} дней\n"
                )


        await context.bot.send_message(
            chat_id=user_id,
            text=text
        )



# ---------- Запуск ----------


def main():

    init_db()


    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("add", add)
    )

    app.add_handler(
        CommandHandler("list", show)
    )

    app.add_handler(
        CommandHandler("delete", delete)
    )


    # каждый день в 9:00

    app.job_queue.run_daily(
        daily,
        datetime.time(9,0)
    )


    print("Бот запущен!")


    app.run_polling()



if __name__ == "__main__":
    main()