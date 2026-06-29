import datetime
import sqlite3

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN = "8780127018:AAFaX48_joQwXUI0I8EwOOfIHkZWElNAOVM"


conn = sqlite3.connect(
    "birthdays.db",
    check_same_thread=False
)

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



def add_birthday_db(user_id, name, day, month):

    cur.execute(
        "INSERT INTO birthdays VALUES (?,?,?,?)",
        (user_id,name,day,month)
    )

    conn.commit()



def get_birthdays(user_id):

    cur.execute(
        "SELECT name,day,month FROM birthdays WHERE user_id=?",
        (user_id,)
    )

    return cur.fetchall()



async def start(update, context):

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "🎂 Бот дней рождения\n\n"
        "/add Имя ДД.ММ\n"
        "/list\n"
        "/delete Имя\n"
        "/test"
    )



async def add(update, context):

    try:

        name=context.args[0]
        date=context.args[1]

        day,month=map(int,date.split("."))

        add_birthday_db(
            update.effective_user.id,
            name,
            day,
            month
        )

        await context.bot.send_message(
            update.effective_chat.id,
            "✅ Добавлено"
        )

    except:

        await context.bot.send_message(
            update.effective_chat.id,
            "❌ /add Имя ДД.ММ"
        )



async def list_cmd(update, context):

    data=get_birthdays(
        update.effective_user.id
    )

    text="🎂 Дни рождения:\n\n"

    today=datetime.date.today()


    for name,day,month in data:

        birthday=datetime.date(
            today.year,
            month,
            day
        )

        delta=(birthday-today).days


        if delta<0:

            birthday=datetime.date(
                today.year+1,
                month,
                day
            )

            delta=(birthday-today).days


        text+=f"{name} {day}.{month} через {delta} дней\n"


    await context.bot.send_message(
        update.effective_chat.id,
        text
    )



async def delete_birthday(update, context):

    name=" ".join(context.args)

    cur.execute(
        "DELETE FROM birthdays WHERE user_id=? AND name=?",
        (
        update.effective_user.id,
        name
        )
    )

    conn.commit()


    await context.bot.send_message(
        update.effective_chat.id,
        f"🗑 Удалено {name}"
    )



async def test(update, context):

    await context.bot.send_message(
        update.effective_chat.id,
        "🧪 Test OK"
    )



async def check_birthdays(context):

    today=datetime.date.today()


    cur.execute(
        "SELECT user_id,name FROM birthdays WHERE day=? AND month=?",
        (
        today.day,
        today.month
        )
    )


    for user_id,name in cur.fetchall():

        await context.bot.send_message(
            user_id,
            f"🎉 Сегодня день рождения у {name}! 🥳"
        )



def main():

    app=Application.builder().token(TOKEN).build()


    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("add",add))
    app.add_handler(CommandHandler("list",list_cmd))
    app.add_handler(CommandHandler("delete",delete_birthday))
    app.add_handler(CommandHandler("test",test))


    app.job_queue.run_daily(
        check_birthdays,
        datetime.time(5,55)
    )


    print("Бот запущен")


    app.run_polling()



if __name__=="__main__":
    main()