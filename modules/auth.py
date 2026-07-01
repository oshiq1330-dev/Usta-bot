from telebot import types
import json
import os
import math

# 🔹 Saqlash
users = {}        # barcha userlar
user_role = {}    # user_id → role
USERS_FILE = "users.json"
SHOPS_FILE = "shops.json"

def get_distance(lat1, lon1, lat2, lon2):

    R = 6371  # Yer radiusi (km)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat/2)**2 +
        math.cos(math.radians(lat1)) *
        math.cos(math.radians(lat2)) *
        math.sin(dlon/2)**2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c  # km

def load_data():

    global users, shops

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    else:
        users = {}

    if os.path.exists(SHOPS_FILE):
        with open(SHOPS_FILE, "r") as f:
            shops = json.load(f)
    else:
        shops = {}

def save_data():

    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

    with open(SHOPS_FILE, "w") as f:
        json.dump(shops, f)


# ================= START =================
def start(user_id, bot):

    # Agar oldin ro‘yxatdan o‘tgan bo‘lsa
    if user_id in user_role:
        return True

    # Aks holda tanlash menyusi
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("👷 Santexnikman", "🏪 Do‘konchiman")
    markup.row("🔎 Santexnik kerak")

    bot.send_message(user_id, "Kim siz?", reply_markup=markup)

    return False


# ================= HANDLE =================
def handle(message, bot):
    user_id = message.chat.id
    text = message.text

    name = message.from_user.first_name
    username = message.from_user.username

    # ---------- USTA ----------
    if text == "👷 Santexnikman":
        user_role[user_id] = "usta"

        users[str(user_id)] = {
            "name": name,
            "username": username,
            "type": "usta"
        }

        save_data()

        bot.send_message(user_id, "✅ Siz usta sifatida ro‘yxatdan o‘tdingiz")
        return True


    # ---------- DO‘KONCHI ----------
    elif text == "🏪 Do‘konchiman":
        user_role[user_id] = "dokonchi"

        users[str(user_id)] = {
            "name": name,
            "username": username,
            "type": "dokonchi"
        }

        save_data()

        bot.send_message(user_id, "✅ Siz do‘konchi sifatida ro‘yxatdan o‘tdingiz")
        return True


    # ---------- MIJOZ ----------
    elif text == "🔎 Santexnik kerak":
        user_role[user_id] = "mijoz"

        bot.send_message(user_id, "🔎 Sizga yaqin ustalar:")
        show_masters(bot, user_id)

        return True

    return False


def find_near_masters(message, bot):
    user_id = message.chat.id

    if not message.location:
        return

    lat = message.location.latitude
    lon = message.location.longitude

    masters = []

    # 📍 masofani hisoblaymiz
    for uid, u in users.items():

        dist = get_distance(lat, lon, u["lat"], u["lon"])

        if dist <= 5:
            masters.append((dist, u, uid))

    # 🔥 ENG MUHIM — SORT
    masters.sort(key=lambda x: x[0])

    text = "👷 Yaqin ustalar:\n\n"

    for dist, u, uid in masters:

        if u.get("username"):
            text += f"{u['name']} ({round(dist,1)} km) → https://t.me/{u['username']}\n"
        else:
            text += f"{u['name']} ({round(dist,1)} km)\n"

    if not masters:
        text = "❌ Yaqin ustalar topilmadi"

    bot.send_message(user_id, text)

load_data()
