import telebot
import sqlite3
import time
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
    ref_by INTEGER DEFAULT 0,
    refs INTEGER DEFAULT 0
)
""")
conn.commit()

# -------- START --------
@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.from_user.id
    args = m.text.split()

    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        ref = int(args[1]) if len(args) > 1 else 0
        cursor.execute("INSERT INTO users(id, ref_by) VALUES(?,?)",(user_id,ref))
        conn.commit()

        if ref != 0 and ref != user_id:
            cursor.execute("UPDATE users SET coins=coins+5, refs=refs+1 WHERE id=?", (ref,))
            conn.commit()
            bot.send_message(ref,"🎉 Referal +5 coin!")

    menu(m.chat.id)

# -------- MENU --------
def menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Ishlash","👤 Profil")
    markup.add("👥 Referal","🛒 Do‘kon")
    markup.add("🎰 O‘yin","🏆 Top")
    markup.add("💎 Almaz yechish")
    bot.send_message(chat_id,"🏠 MENU",reply_markup=markup)

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
        telebot.types.InlineKeyboardButton("💎 Convert",callback_data="convert")
    )
    bot.send_message(m.chat.id,"💰 Ishlash",reply_markup=markup)

# -------- COIN --------
@bot.callback_query_handler(func=lambda c:c.data=="coin")
def coin(c):
    cursor.execute("UPDATE users SET coins=coins+1 WHERE id=?", (c.from_user.id,))
    conn.commit()

    cursor.execute("SELECT coins, diamonds FROM users WHERE id=?", (c.from_user.id,))
    coins, dia = cursor.fetchone()

    bot.answer_callback_query(c.id,f"💰 {coins} | 💎 {dia}")

# -------- BONUS --------
@bot.callback_query_handler(func=lambda c:c.data=="bonus")
def bonus(c):
    cursor.execute("UPDATE users SET coins=coins+5 WHERE id=?", (c.from_user.id,))
    conn.commit()
    bot.answer_callback_query(c.id,"🎁 +5 coin")

# -------- CONVERT --------
@bot.callback_query_handler(func=lambda c:c.data=="convert")
def convert(c):
    cursor.execute("SELECT coins FROM users WHERE id=?", (c.from_user.id,))
    coins = cursor.fetchone()[0]

    if coins>=100:
        cursor.execute("UPDATE users SET coins=coins-100, diamonds=diamonds+10 WHERE id=?", (c.from_user.id,))
        conn.commit()
        bot.answer_callback_query(c.id,"💎 +10 almaz")
    else:
        bot.answer_callback_query(c.id,"❌ 100 coin kerak",True)

# -------- REFERAL --------
@bot.message_handler(func=lambda m: m.text=="👥 Referal")
def ref(m):
    cursor.execute("SELECT refs FROM users WHERE id=?", (m.from_user.id,))
    refs = cursor.fetchone()[0]

    link = f"https://t.me/{bot.get_me().username}?start={m.from_user.id}"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📢 Do‘st taklif qilish", url=link))

    bot.send_message(m.chat.id,
f"""👥 REFERAL

👥 Taklif qilingan: {refs}
💰 Har biri: +5 coin

🔗 Havola:
{link}
""",reply_markup=markup)

# -------- SLOT --------
@bot.message_handler(func=lambda m: m.text=="🎰 O‘yin")
def game(m):
    res = [random.choice(["7","🍒","⭐"]) for _ in range(3)]

    if res.count("7")==3:
        cursor.execute("UPDATE users SET coins=coins+20 WHERE id=?", (m.from_user.id,))
        conn.commit()
        result = "🎉 +20 coin"
    else:
        result = "😢 Yutmadi"

    bot.send_message(m.chat.id,f"🎰 {' | '.join(res)}\n{result}")

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
    markup = telebot.types.InlineKeyboardMarkup()

    markup.add(telebot.types.InlineKeyboardButton("💎 100 = 13k",callback_data="buy_100"))
    markup.add(telebot.types.InlineKeyboardButton("💎 310 = 40k",callback_data="buy_310"))
    markup.add(telebot.types.InlineKeyboardButton("💎 520 = 65k",callback_data="buy_520"))

    markup.add(telebot.types.InlineKeyboardButton("📅 Haftalik 28k",callback_data="buy_week"))
    markup.add(telebot.types.InlineKeyboardButton("📅 Oylik 120k",callback_data="buy_month"))

    markup.add(telebot.types.InlineKeyboardButton("⚡ EVO 3 kun 10k",callback_data="buy_evo3"))
    markup.add(telebot.types.InlineKeyboardButton("⚡ EVO 7 kun 15k",callback_data="buy_evo7"))
    markup.add(telebot.types.InlineKeyboardButton("⚡ EVO 30 kun 40k",callback_data="buy_evo30"))

    bot.send_message(m.chat.id,"🛒 Tanlang:",reply_markup=markup)

@bot.callback_query_handler(func=lambda c:c.data.startswith("buy_"))
def buy(c):
    user = c.from_user
    username = f"@{user.username}" if user.username else "yo‘q"

    bot.send_message(ADMIN_ID,
f"""🛒 BUY

👤 {username}
🆔 {user.id}
🔗 https://t.me/{user.username}

📦 {c.data}
""")

    bot.send_message(c.message.chat.id,"✅ Admin yozadi")

# -------- WD --------
@bot.message_handler(func=lambda m: m.text=="💎 Almaz yechish")
def wd(m):
    cursor.execute("SELECT diamonds FROM users WHERE id=?", (m.from_user.id,))
    dia = cursor.fetchone()[0]

    if dia < 100:
        bot.send_message(m.chat.id,"❌ 100 almaz yig‘ing")
        return

    bot.send_message(m.chat.id,"🎮 ID kiriting:")
    bot.register_next_step_handler(m,send_wd)

def send_wd(m):
    user = m.from_user
    username = f"@{user.username}" if user.username else "yo‘q"

    bot.send_message(ADMIN_ID,
f"""💎 YECHISH

👤 {username}
🆔 {user.id}
🔗 https://t.me/{user.username}

🎮 ID: {m.text}
""")

    bot.send_message(m.chat.id,"✅ Yuborildi")

print("FINAL PRO BOT 🚀")
bot.infinity_polling()
