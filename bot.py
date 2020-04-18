import sys
import mysql.connector
import telebot
from table import *
from mysql.connector import errorcode
import pika
from telebot import types
from flask import Flask
from elasticsearch import Elasticsearch

bot = telebot.TeleBot("1022366836:AAHUlel-Ewl7ofp6yqCpc1n6DT0vL7zmyCs")

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        port="3306",
        database="test"
    )

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
        sys.exit()
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
        sys.exit()
    else:
        print(err)
        sys.exit()

# es = Elasticsearch("localhost: 3306")
# table_books = db['orders']

cursor = db.cursor()
# cursor.execute("DROP TABLE orders;")
# cursor.execute("CREATE TABLE orders ("
#                "id int AUTO_INCREMENT PRIMARY KEY,"
#                "user_id char(20), "
#                "username varchar(50),"
#                "location varchar(10), "
#                "room char(15), "
#                "payment int, "
#                "details varchar(50), "
#                "delivery_guy varchar(50) DEFAULT '')")
user_data = {}


# user_id   username   location(kbtu or dormitory)    room    payment   details   delivery_guy


# @bot.message_handler(commands=['url'])
# def start(message):
#     markup = types.InlineKeyboardMarkup()
#     btn_my_site = types.InlineKeyboardButton(text='Наш сайт')
#     btn_my_site1 = types.InlineKeyboardButton(text='Наш сайт', url='https://habrahabr.ru')
#     markup.add(btn_my_site)
#     markup.add(btn_my_site1)
#     bot.send_message(message.chat.id, "Нажми на кнопку и перейди на наш сайт.", reply_markup=markup)


@bot.message_handler(commands=['order'])
def send_welcome(message):
    msg = bot.send_message(message.chat.id, "Ready to take your order. Enter location: [KBTU or DORMITORY]")
    bot.register_next_step_handler(msg, process_location_step)


def process_location_step(message):
    try:
        user_id = message.from_user.id
        user_data[user_id] = Order(message.text)
        user = user_data[user_id]
        user.location = message.text
        msg = bot.send_message(message.chat.id, "Enter room:")
        bot.register_next_step_handler(msg, process_room_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_room_step(message):
    try:
        user_id = message.from_user.id
        user = user_data[user_id]
        user.room = message.text
        msg = bot.send_message(message.chat.id, "Enter details:")
        bot.register_next_step_handler(msg, process_details_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_details_step(message):
    try:
        user_id = message.from_user.id
        user = user_data[user_id]
        user.details = message.text
        msg = bot.send_message(message.chat.id, "Enter payment[tenge]:")
        bot.register_next_step_handler(msg, process_payment_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_payment_step(message):
    try:
        user_id = message.from_user.id
        user = user_data[user_id]
        user.username = message.from_user.username
        user.payment = message.text
        sql = "INSERT INTO orders (user_id, username, location, room, details, payment) \
                                  VALUES (%s, %s, %s, %s, %s, %s)"
        val = (user_id, user.username, user.location, str(user.room), str(user.details), int(user.payment))
        print(val)
        cursor.execute(sql, val)
        db.commit()
        bot.send_message(message.chat.id, "Your order successfully added!")
    except Exception as e:
        bot.reply_to(message, 'Error!')
        print(e)


# list orders to do
@bot.message_handler(commands=['do_order'])
def send_welcome(message):
    try:
        # es.get(index="search_degital_library", doc_type="categories", id=2)
        # es.sesarch(index="search", doc_type="categories", body={"query": {"match_all": {}}})
        sql = "SELECT * FROM orders"
        cursor.execute(sql)
        result = cursor.fetchall()
        for i in range(len(result)):
            sending_orders(message.chat.id, result[i])
        msg = bot.send_message(message.chat.id, "Ready to take order?")
        bot.register_next_step_handler(msg, process_delivery_guy_step)
    except Exception as e:
        bot.reply_to(message, 'Error')
        print(e)


def process_delivery_guy_step(message):
    try:
        user_id = message.from_user.id
        user_data[user_id] = Order(message.text)
        user = user_data[user_id]
        chosen = int(message.text)
        user.delivery_guy = message.from_user.username
        # print(es.get(index="search", doc_type="orders", id=chosen))
        sql = "UPDATE orders SET delivery_guy=(%s) WHERE id=(%s);"
        val = (str(user.delivery_guy), chosen)
        cursor.execute(sql, val)

        cursor.execute("SELECT user_id FROM orders WHERE id='%s'" % chosen)
        result = cursor.fetchone()
        for i in range(len(result)):
            bot.send_message(result[i], "Your delivery guy is" + ' ' + '@' + user.delivery_guy)

        bot.send_message(message.chat.id, "You already have chosen order!")
        db.commit()
    except Exception as e:
        bot.reply_to(message, 'Error!')
        print(e)


def sending_orders(chat, s):
    if s[7] == '':
        bot.send_message(chat,
                         '[' + str(s[0]) + ']' + '[' + str(s[3]) + ' ' + str(s[4]) + '] ' + 'Details: ' + str(
                             s[6]) + ' ' + str(s[5]) + 'KZT')


# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()

if __name__ == '__main__':
    bot.polling(none_stop=True)
