import telebot
import sqlite3
import time
import threading

TOKEN = "8794647398:AAEStXVxs3IQqOADjBsRM8ZfmL_o8UHZ29o"
ADMIN_ID = 8421764297
CHANNEL = "@uzbservic1"

bot = telebot.TeleBot(TOKEN)

# DATABASE
conn = sqlite3.connect("game.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0,
    diamonds INTEGER DEFAULT 0,
    invited_by INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    last_day INTEGER DEFAULT 0
)
""")
conn.commit()

# OBUNA
def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status != "left"
    except:
        return False

# START
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if not check_sub(user_id):
        bot.send_message(message.chat.id, f"❌ Kanalga obuna bo‘ling:\n{CHANNEL}")
        return

    args = message.text.split()

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if user is None:
        ref = int(args[1]) if len(args) > 1 else 0

        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                       (user_id, 0, 0, ref, 0, int(time.time())))
        conn.commit()

        if ref != 0:
            cursor.execute("UPDATE users SET coins = coins + 10 WHERE user_id=?", (ref,))
            conn.commit()
            bot.send_message(ref, "🎉 Siz referal orqali +10 coin oldingiz!")

    menu(message.chat.id)

# MENU
def menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 O‘yin", "📊 Balans")
    markup.add("🛒 Do‘kon")

    bot.send_message(chat_id, "🏠 Asosiy menyu", reply_markup=markup)

# O‘YIN
@bot.message_handler(func=lambda m: m.text == "🎮 O‘yin")
def game(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Tanga bosish")
    markup.add("⚡ Auto coin", "👥 Referal")
    markup.add("🔄 Almazga aylantirish", "🔙 Orqaga")

    bot.send_message(message.chat.id, "🎮 O‘yin bo‘limi", reply_markup=markup)

# CLICK
@bot.message_handler(func=lambda m: m.text == "💰 Tanga bosish")
def click(message):
    user_id = message.from_user.id

    cursor.execute("SELECT clicks, last_day, coins FROM users WHERE user_id=?", (user_id,))
    clicks, last_day, coins = cursor.fetchone()

    now = int(time.time())

    if now - last_day > 86400:
        clicks = 0
        cursor.execute("UPDATE users SET clicks=0, last_day=? WHERE user_id=?", (now, user_id))
        conn.commit()

    if clicks >= 50:
        bot.send_message(message.chat.id, "❌ Bugungi limit tugadi (50)")
        return

    cursor.execute("UPDATE users SET coins=coins+1, clicks=clicks+1 WHERE user_id=?", (user_id,))
    conn.commit()

    bot.send_message(message.chat.id, f"💰 Coin: {coins+1} | {clicks+1}/50")

# AUTOCOIN (SAFE)
def auto_coin():
    while True:
        time.sleep(3600)  # har 1 soat
        conn2 = sqlite3.connect("game.db")
        cur = conn2.cursor()

        cur.execute("UPDATE users SET coins = coins + 1")
        conn2.commit()
        conn2.close()

threading.Thread(target=auto_coin, daemon=True).start()

# REFERAL
@bot.message_handler(func=lambda m: m.text == "👥 Referal")
def ref(message):
    link = f"https://t.me/{bot.get_me().username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, f"👥 Linkingiz:\n{link}\n+10 coin har odam")

# BALANS
@bot.message_handler(func=lambda m: m.text == "📊 Balans")
def balance(message):
    cursor.execute("SELECT coins, diamonds FROM users WHERE user_id=?", (message.from_user.id,))
    coins, diamonds = cursor.fetchone()

    bot.send_message(message.chat.id, f"💰 Coin: {coins}\n💎 Almaz: {diamonds}")

# CONVERT
@bot.message_handler(func=lambda m: m.text == "🔄 Almazga aylantirish")
def convert(message):
    user_id = message.from_user.id

    cursor.execute("SELECT coins, diamonds FROM users WHERE user_id=?", (user_id,))
    coins, diamonds = cursor.fetchone()

    if coins >= 10:
        coins -= 10
        diamonds += 1

        cursor.execute("UPDATE users SET coins=?, diamonds=? WHERE user_id=?", (coins, diamonds, user_id))
        conn.commit()

        bot.send_message(message.chat.id, "💎 1 almaz olindi")
    else:
        bot.send_message(message.chat.id, "❌ 10 coin kerak")

# SHOP
@bot.message_handler(func=lambda m: m.text == "🛒 Do‘kon")
def shop(message):
    markup = telebot.types.InlineKeyboardMarkup()

    markup.add(telebot.types.InlineKeyboardButton("💎 100+10 = 13k", callback_data="100"))
    markup.add(telebot.types.InlineKeyboardButton("💎 310+31 = 40k", callback_data="310"))
    markup.add(telebot.types.InlineKeyboardButton("💎 520+52 = 65k", callback_data="520"))
    markup.add(telebot.types.InlineKeyboardButton("💎 1060+106 = 135k", callback_data="1060"))

    markup.add(telebot.types.InlineKeyboardButton("🎟 3 kun = 10k", callback_data="3"))
    markup.add(telebot.types.InlineKeyboardButton("🎟 7 kun = 15k", callback_data="7"))
    markup.add(telebot.types.InlineKeyboardButton("🎟 30 kun = 40k", callback_data="30"))

    bot.send_message(message.chat.id, "🛒 Do‘kon", reply_markup=markup)

# BUY
@bot.callback_query_handler(func=lambda call: True)
def buy(call):
    user = call.from_user

    bot.send_message(ADMIN_ID,
                     f"🛒 Buyurtma\n👤 @{user.username}\nID:{user.id}\n📦 {call.data}")

    bot.send_message(call.message.chat.id, "✅ Admin siz bilan bog‘lanadi")

# ORQAGA
@bot.message_handler(func=lambda m: m.text == "🔙 Orqaga")
def back(message):
    menu(message.chat.id)

print("Bot ishlayapti...")
bot.infinity_polling()
