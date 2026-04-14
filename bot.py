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
    game_limit INTEGER DEFAULT 0,
    ref_by INTEGER DEFAULT 0
)
""")
conn.commit()

# -------- SUB CHECK --------
def check_sub(user_id):
    try:
        return bot.get_chat_member(CHANNEL, user_id).status in ["member","administrator","creator"]
    except:
        return False

# -------- START --------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users(id) VALUES(?)", (user_id,))
        conn.commit()

    if not check_sub(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📢 Obuna", url=f"https://t.me/{CHANNEL[1:]}"),
            telebot.types.InlineKeyboardButton("✅ Tekshirish", callback_data="check")
        )
        bot.send_message(message.chat.id, "❌ Kanalga obuna bo‘ling!", reply_markup=markup)
        return

    menu(message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data=="check")
def check(c):
    if check_sub(c.from_user.id):
        bot.send_message(c.message.chat.id, "✅ Tasdiqlandi!")
        menu(c.message.chat.id)

# -------- MENU --------
def menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Ishlash","👤 Profil")
    markup.add("👥 Referal","🛒 Do‘kon")
    markup.add("🎰 O‘yin","🏆 Top")
    markup.add("💎 Almaz yechish")
    bot.send_message(chat_id,"🏠 Asosiy menyu",reply_markup=markup)

# -------- PROFIL --------
@bot.message_handler(func=lambda m: m.text=="👤 Profil")
def profil(m):
    user = m.from_user
    username = f"@{user.username}" if user.username else "yo‘q"

    cursor.execute("SELECT coins, diamonds FROM users WHERE id=?", (user.id,))
    coins, dia = cursor.fetchone()

    bot.send_message(m.chat.id,
f"""👤 PROFIL

👤 {username}
🆔 {user.id}

💰 Coin: {coins}
💎 Almaz: {dia}

📞 Admin: @elxon1312
""")

# -------- ISHLASH --------
@bot.message_handler(func=lambda m: m.text=="💰 Ishlash")
def earn(m):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🪙 Bosish",callback_data="coin"),
        telebot.types.InlineKeyboardButton("🎁 Bonus",callback_data="bonus"),
        telebot.types.InlineKeyboardButton("💎 Almazga aylantirish",callback_data="convert")
    )
    bot.send_message(m.chat.id,"💰 Ishlash bo‘limi",reply_markup=markup)

# -------- COIN --------
@bot.callback_query_handler(func=lambda c:c.data=="coin")
def coin(c):
    cursor.execute("UPDATE users SET coins=coins+1 WHERE id=?", (c.from_user.id,))
    conn.commit()
    bot.answer_callback_query(c.id,"🪙 +1 coin")

# -------- BONUS --------
@bot.callback_query_handler(func=lambda c:c.data=="bonus")
def bonus(c):
    now = int(time.time())
    cursor.execute("SELECT last_bonus FROM users WHERE id=?", (c.from_user.id,))
    last = cursor.fetchone()[0]

    if now-last>=86400:
        cursor.execute("UPDATE users SET coins=coins+5,last_bonus=? WHERE id=?", (now,c.from_user.id))
        conn.commit()
        bot.answer_callback_query(c.id,"🎁 +5 coin")
    else:
        bot.answer_callback_query(c.id,"❌ Bugun oldingiz",True)

# -------- CONVERT --------
@bot.callback_query_handler(func=lambda c:c.data=="convert")
def convert(c):
    cursor.execute("SELECT coins FROM users WHERE id=?", (c.from_user.id,))
    coins = cursor.fetchone()[0]

    if coins>=10:
        cursor.execute("UPDATE users SET coins=coins-10, diamonds=diamonds+1 WHERE id=?", (c.from_user.id,))
        conn.commit()
        bot.answer_callback_query(c.id,"💎 1 almaz oldingiz!")
    else:
        bot.answer_callback_query(c.id,"❌ 10 coin kerak",True)

# -------- REFERAL --------
@bot.message_handler(func=lambda m: m.text=="👥 Referal")
def ref(m):
    link = f"https://t.me/{bot.get_me().username}?start={m.from_user.id}"
    bot.send_message(m.chat.id,
f"""👥 REFERAL

🔗 Havola:
{link}

📢 Do‘stlarni taklif qiling va coin oling!
""")

# -------- SLOT --------
@bot.message_handler(func=lambda m: m.text=="🎰 O‘yin")
def game(m):
    cursor.execute("SELECT game_limit FROM users WHERE id=?", (m.from_user.id,))
    limit = cursor.fetchone()[0]

    if limit>=10:
        bot.send_message(m.chat.id,"❌ Bugungi limit tugadi")
        return

    res = [random.choice(["7","🍒","⭐"]) for _ in range(3)]
    text = " | ".join(res)

    if res.count("7")==3:
        cursor.execute("UPDATE users SET coins=coins+3 WHERE id=?", (m.from_user.id,))
        result = "🎉 YUTDI +3 coin"
    else:
        result = "😢 Yutmadi"

    cursor.execute("UPDATE users SET game_limit=game_limit+1 WHERE id=?", (m.from_user.id,))
    conn.commit()

    bot.send_message(m.chat.id,f"🎰 {text}\n{result}")

# -------- TOP --------
@bot.message_handler(func=lambda m: m.text=="🏆 Top")
def top(m):
    cursor.execute("SELECT id,coins FROM users ORDER BY coins DESC LIMIT 5")
    data = cursor.fetchall()

    text="🏆 TOP\n\n"
    for i,u in enumerate(data,1):
        text+=f"{i}. {u[0]} ({u[0]}) — {u[1]} coin\n"

    bot.send_message(m.chat.id,text)

# -------- SHOP --------
@bot.message_handler(func=lambda m: m.text=="🛒 Do‘kon")
def shop(m):
    bot.send_message(m.chat.id,
"""🛒 DO‘KON

💎 100 = 13.000
💎 310 = 40.000
💎 520 = 65.000

📅 Haftalik = 28.000
📅 Oylik = 120.000

📞 Sotib olish: @elxon1312
""")

# -------- WD --------
@bot.message_handler(func=lambda m: m.text=="💎 Almaz yechish")
def wd(m):
    bot.send_message(m.chat.id,"🎮 O‘yin ID kiriting:")
    bot.register_next_step_handler(m,send_wd)

def send_wd(m):
    bot.send_message(ADMIN_ID,f"💎 YECHISH\n🆔 {m.from_user.id}\n🎮 ID: {m.text}")
    bot.send_message(m.chat.id,"✅ Yuborildi")

print("PRO BOT ISHLAYAPTI 🚀")
bot.infinity_polling()
