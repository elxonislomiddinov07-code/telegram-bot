import telebot
import sqlite3
import time
import threading
import random

TOKEN = "8794647398:AAEStXVxs3IQqOADjBsRM8ZfmL_o8UHZ29o"
ADMIN_ID = 8421764297
CHANNEL = "@uzbservic1"

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0,
    diamonds INTEGER DEFAULT 0,
    last_bonus INTEGER DEFAULT 0,
    last_click INTEGER DEFAULT 0,
    autocoin INTEGER DEFAULT 0,
    ref_by INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------------- CHECK SUB ----------------
def check_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()

    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        ref = int(args[1]) if len(args) > 1 else 0
        cursor.execute("INSERT INTO users(id, ref_by) VALUES(?,?)", (user_id, ref))
        conn.commit()

        if ref != 0 and ref != user_id:
            cursor.execute("UPDATE users SET coins=coins+10 WHERE id=?", (ref,))
            conn.commit()
            bot.send_message(ref, "🎉 Referal +10 coin!")

    if not check_sub(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📢 Obuna", url=f"https://t.me/{CHANNEL[1:]}"),
            telebot.types.InlineKeyboardButton("✅ Tekshirish", callback_data="check")
        )
        bot.send_message(message.chat.id, "❌ Kanalga obuna bo‘ling!", reply_markup=markup)
        return

    menu(message.chat.id)

# ---------------- CHECK ----------------
@bot.callback_query_handler(func=lambda call: call.data == "check")
def check(call):
    if check_sub(call.from_user.id):
        bot.send_message(call.message.chat.id, "✅ Tasdiqlandi!")
        menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Obuna bo‘ling!", True)

# ---------------- MENU ----------------
def menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Ishlash", "👤 Profil")
    markup.add("👥 Referal", "🛒 Do‘kon")
    markup.add("🎮 O‘yin", "🏆 Top")
    markup.add("💸 Pul yechish")

    bot.send_message(chat_id, "🏠 MENU", reply_markup=markup)

# ---------------- PROFIL ----------------
@bot.message_handler(func=lambda m: m.text == "👤 Profil")
def profile(message):
    cursor.execute("SELECT coins, diamonds FROM users WHERE id=?", (message.from_user.id,))
    coins, diamonds = cursor.fetchone()
    bot.send_message(message.chat.id, f"👤 Profil\n💰 {coins}\n💎 {diamonds}")

# ---------------- EARN ----------------
@bot.message_handler(func=lambda m: m.text == "💰 Ishlash")
def earn(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🪙 Coin", callback_data="coin"),
        telebot.types.InlineKeyboardButton("🎁 Bonus", callback_data="bonus"),
        telebot.types.InlineKeyboardButton("⚡ Autocoin", callback_data="auto")
    )
    bot.send_message(message.chat.id, "💰 Ishlash", reply_markup=markup)

# ---------------- COIN ----------------
@bot.callback_query_handler(func=lambda call: call.data == "coin")
def coin(call):
    user_id = call.from_user.id
    now = int(time.time())

    cursor.execute("SELECT last_click FROM users WHERE id=?", (user_id,))
    last = cursor.fetchone()[0]

    if now - last < 2:
        bot.answer_callback_query(call.id, "⏳ Sekinroq!")
        return

    cursor.execute("UPDATE users SET coins=coins+1, last_click=? WHERE id=?", (now, user_id))
    conn.commit()

    bot.answer_callback_query(call.id, "🪙 +1")

# ---------------- BONUS ----------------
@bot.callback_query_handler(func=lambda call: call.data == "bonus")
def bonus(call):
    user_id = call.from_user.id
    now = int(time.time())

    cursor.execute("SELECT last_bonus FROM users WHERE id=?", (user_id,))
    last = cursor.fetchone()[0]

    if now - last >= 86400:
        cursor.execute("UPDATE users SET coins=coins+5, last_bonus=? WHERE id=?", (now, user_id))
        conn.commit()
        bot.answer_callback_query(call.id, "🎁 +5 coin!")
    else:
        bot.answer_callback_query(call.id, "❌ Oldingiz", True)

# ---------------- AUTO ----------------
@bot.callback_query_handler(func=lambda call: call.data == "auto")
def auto(call):
    cursor.execute("UPDATE users SET autocoin=1 WHERE id=?", (call.from_user.id,))
    conn.commit()
    bot.answer_callback_query(call.id, "⚡ Yoqildi!")

def auto_worker():
    while True:
        cursor.execute("SELECT id FROM users WHERE autocoin=1")
        users = cursor.fetchall()

        for u in users:
            uid = u[0]
            cursor.execute("UPDATE users SET coins=coins+1 WHERE id=?", (uid,))
            conn.commit()
            try:
                bot.send_message(uid, "⚡ +1 coin")
            except:
                pass

        time.sleep(3600)

threading.Thread(target=auto_worker).start()

# ---------------- REFERAL ----------------
@bot.message_handler(func=lambda m: m.text == "👥 Referal")
def ref(message):
    link = f"https://t.me/{bot.get_me().username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, link)

# ---------------- REFERAL MINUS ----------------
def check_unsub():
    while True:
        cursor.execute("SELECT id, ref_by FROM users WHERE ref_by!=0")
        users = cursor.fetchall()

        for user_id, ref in users:
            if not check_sub(user_id):
                cursor.execute("UPDATE users SET ref_by=0 WHERE id=?", (user_id,))
                cursor.execute("UPDATE users SET coins=coins-10 WHERE id=?", (ref,))
                conn.commit()
                try:
                    bot.send_message(ref, "❌ Referal chiqdi -10 coin")
                except:
                    pass

        time.sleep(60)

threading.Thread(target=check_unsub).start()

# ---------------- GAME ----------------
@bot.message_handler(func=lambda m: m.text == "🎮 O‘yin")
def game(message):
    if random.choice([True, False]):
        cursor.execute("UPDATE users SET coins=coins+3 WHERE id=?", (message.from_user.id,))
        conn.commit()
        bot.send_message(message.chat.id, "🎉 +3 coin")
    else:
        bot.send_message(message.chat.id, "😢 Yutqazding")

# ---------------- TOP ----------------
@bot.message_handler(func=lambda m: m.text == "🏆 Top")
def top(message):
    cursor.execute("SELECT id, coins FROM users ORDER BY coins DESC LIMIT 5")
    data = cursor.fetchall()

    text = "🏆 TOP\n"
    for i, u in enumerate(data, 1):
        text += f"{i}. {u[0]} — {u[1]}\n"

    bot.send_message(message.chat.id, text)

# ---------------- SHOP ----------------
@bot.message_handler(func=lambda m: m.text == "🛒 Do‘kon")
def shop(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("💎 100", callback_data="buy_100"),
        telebot.types.InlineKeyboardButton("📅 Haftalik", callback_data="buy_week")
    )
    bot.send_message(message.chat.id, "🛒 Do‘kon", reply_markup=markup)

# ---------------- BUY ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy"))
def buy(call):
    user = call.from_user
    username = user.username if user.username else "yo‘q"

    bot.send_message(ADMIN_ID,
        f"🛒 BUY\n👤 @{username}\n🆔 {user.id}\n📦 {call.data}"
    )
    bot.send_message(call.message.chat.id, "✅ Admin yozadi")

# ---------------- WITHDRAW ----------------
@bot.message_handler(func=lambda m: m.text == "💸 Pul yechish")
def withdraw(message):
    bot.send_message(message.chat.id, "💳 Ma'lumot yubor:")
    bot.register_next_step_handler(message, get_wd)

def get_wd(message):
    user = message.from_user
    username = user.username if user.username else "yo‘q"

    bot.send_message(ADMIN_ID,
        f"💸 WD\n👤 @{username}\n🆔 {user.id}\n📩 {message.text}"
    )
    bot.send_message(message.chat.id, "✅ Yuborildi")

# ---------------- BROADCAST ----------------
@bot.message_handler(commands=['send'])
def send_all(message):
    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(message.chat.id, "Xabar yoz")
    bot.register_next_step_handler(message, broadcast)

def broadcast(message):
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            bot.send_message(u[0], message.text)
        except:
            pass

# ---------------- RUN ----------------
print("BOT PRO ISHLAYAPTI 🚀")
bot.infinity_polling()
