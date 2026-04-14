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
    last_bonus INTEGER DEFAULT 0,
    daily_click INTEGER DEFAULT 0,
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
    args = message.text.split()

    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        ref = int(args[1]) if len(args) > 1 else 0
        cursor.execute("INSERT INTO users(id, ref_by) VALUES(?,?)",(user_id,ref))
        conn.commit()

        if ref != 0 and ref != user_id:
            cursor.execute("UPDATE users SET coins=coins+10 WHERE id=?", (ref,))
            conn.commit()
            bot.send_message(ref,"🎉 Yangi referal +10 coin!")

    if not check_sub(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📢 Obuna", url=f"https://t.me/{CHANNEL[1:]}"),
            telebot.types.InlineKeyboardButton("✅ Tekshirish", callback_data="check")
        )
        bot.send_message(message.chat.id,"❌ Kanalga obuna bo‘ling!",reply_markup=markup)
        return

    menu(message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data=="check")
def check(c):
    if check_sub(c.from_user.id):
        bot.send_message(c.message.chat.id,"✅ Tasdiqlandi!")
        menu(c.message.chat.id)

# -------- MENU --------
def menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Ishlash","👤 Profil")
    markup.add("👥 Referal","🛒 Do‘kon")
    markup.add("🎰 O‘yin","🏆 Top")
    markup.add("💎 Almaz yechish")
    bot.send_message(chat_id,"🏠 ASOSIY MENU",reply_markup=markup)

# -------- PROFIL --------
@bot.message_handler(func=lambda m: m.text=="👤 Profil")
def profil(m):
    user = m.from_user
    username = f"@{user.username}" if user.username else "yo‘q"

    cursor.execute("SELECT coins, diamonds FROM users WHERE id=?", (user.id,))
    coins, dia = cursor.fetchone()

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📞 Admin bilan bog‘lanish", url="https://t.me/elxon1312"))

    bot.send_message(m.chat.id,
f"""👤 PROFIL

👤 {username}
🆔 {user.id}

💰 Coin: {coins}
💎 Almaz: {dia}
""",reply_markup=markup)

# -------- ISHLASH --------
@bot.message_handler(func=lambda m: m.text=="💰 Ishlash")
def earn(m):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🪙 Bosish",callback_data="coin"),
        telebot.types.InlineKeyboardButton("🎁 Bonus",callback_data="bonus"),
        telebot.types.InlineKeyboardButton("💎 Almazga aylantirish",callback_data="convert")
    )
    bot.send_message(m.chat.id,"💰 Ishlash",reply_markup=markup)

# -------- COIN --------
@bot.callback_query_handler(func=lambda c:c.data=="coin")
def coin(c):
    cursor.execute("SELECT daily_click FROM users WHERE id=?", (c.from_user.id,))
    count = cursor.fetchone()[0]

    if count >= 50:
        bot.answer_callback_query(c.id,"❌ Kunlik limit tugadi")
        return

    cursor.execute("UPDATE users SET coins=coins+1,daily_click=daily_click+1 WHERE id=?", (c.from_user.id,))
    conn.commit()
    bot.answer_callback_query(c.id,f"🪙 +1 ({50-count-1} qoldi)")

# -------- CONVERT --------
@bot.callback_query_handler(func=lambda c:c.data=="convert")
def convert(c):
    cursor.execute("SELECT coins FROM users WHERE id=?", (c.from_user.id,))
    coins = cursor.fetchone()[0]

    if coins>=10:
        cursor.execute("UPDATE users SET coins=coins-10, diamonds=diamonds+1 WHERE id=?", (c.from_user.id,))
        conn.commit()
        bot.answer_callback_query(c.id,"💎 1 almaz")
    else:
        bot.answer_callback_query(c.id,"❌ 10 coin kerak",True)

# -------- REFERAL --------
@bot.message_handler(func=lambda m: m.text=="👥 Referal")
def ref(m):
    link = f"https://t.me/{bot.get_me().username}?start={m.from_user.id}"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📢 Do‘stlarni taklif qilish", url=link))

    bot.send_message(m.chat.id,f"🔗 Sizning havola:\n{link}",reply_markup=markup)

# -------- REFERAL CHECK --------
def check_unsub():
    while True:
        cursor.execute("SELECT id, ref_by FROM users WHERE ref_by!=0")
        users = cursor.fetchall()

        for uid, ref in users:
            if not check_sub(uid):
                cursor.execute("UPDATE users SET ref_by=0 WHERE id=?", (uid,))
                cursor.execute("UPDATE users SET coins=coins-10 WHERE id=?", (ref,))
                conn.commit()

                try:
                    bot.send_message(ref,"❌ Referalingiz chiqib ketdi (-10 coin)")
                except:
                    pass

        time.sleep(60)

import threading
threading.Thread(target=check_unsub).start()

# -------- SLOT --------
@bot.message_handler(func=lambda m: m.text=="🎰 O‘yin")
def game(m):
    cursor.execute("SELECT game_limit FROM users WHERE id=?", (m.from_user.id,))
    limit = cursor.fetchone()[0]

    if limit>=10:
        bot.send_message(m.chat.id,"❌ Limit tugadi")
        return

    res = [random.choice(["7","🍒","⭐"]) for _ in range(3)]

    if res.count("7")==3:
        cursor.execute("UPDATE users SET coins=coins+20 WHERE id=?", (m.from_user.id,))
        result = "🎉 JACKPOT +20 coin!"
    else:
        result = "😢 Yutmadi"

    cursor.execute("UPDATE users SET game_limit=game_limit+1 WHERE id=?", (m.from_user.id,))
    conn.commit()

    bot.send_message(m.chat.id,f"🎰 {' | '.join(res)}\n{result}\nQoldi: {10-limit-1}")

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
    markup.add(
        telebot.types.InlineKeyboardButton("💎 100",callback_data="buy_100"),
        telebot.types.InlineKeyboardButton("💎 310",callback_data="buy_310"),
        telebot.types.InlineKeyboardButton("💎 520",callback_data="buy_520")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("📅 Haftalik",callback_data="buy_week"),
        telebot.types.InlineKeyboardButton("📅 Oylik",callback_data="buy_month")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("⚡ EVO 3 kun",callback_data="buy_evo3"),
        telebot.types.InlineKeyboardButton("⚡ EVO 7 kun",callback_data="buy_evo7"),
        telebot.types.InlineKeyboardButton("⚡ EVO 30 kun",callback_data="buy_evo30")
    )

    bot.send_message(m.chat.id,"🛒 Tanlang:",reply_markup=markup)

@bot.callback_query_handler(func=lambda c:c.data.startswith("buy_"))
def buy(c):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Olaman",callback_data=f"confirm_{c.data}"),
        telebot.types.InlineKeyboardButton("❌ Bekor",callback_data="cancel")
    )
    bot.send_message(c.message.chat.id,"Xarid qilmoqchimisiz?",reply_markup=markup)

@bot.callback_query_handler(func=lambda c:c.data.startswith("confirm_"))
def confirm(c):
    bot.send_message(ADMIN_ID,f"🛒 BUY\n{c.from_user.id}\n{c.data}")
    bot.send_message(c.message.chat.id,"✅ Admin tez orada yozadi")

@bot.callback_query_handler(func=lambda c:c.data=="cancel")
def cancel(c):
    menu(c.message.chat.id)

# -------- WD --------
@bot.message_handler(func=lambda m: m.text=="💎 Almaz yechish")
def wd(m):
    cursor.execute("SELECT diamonds FROM users WHERE id=?", (m.from_user.id,))
    dia = cursor.fetchone()[0]

    if dia < 100:
        bot.send_message(m.chat.id,"❌ 100 almaz kerak")
        return

    bot.send_message(m.chat.id,"🎮 ID yubor:")
    bot.register_next_step_handler(m,send_wd)

def send_wd(m):
    bot.send_message(ADMIN_ID,f"💎 YECHISH\n{m.from_user.id}\nID: {m.text}")
    bot.send_message(m.chat.id,"✅ Yuborildi")

print("ULTRA PRO BOT 🚀")
bot.infinity_polling()
