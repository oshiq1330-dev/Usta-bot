from telebot import types
import math
from core.formatter import format_result
from core.engine import process
from core.formulas import HAMMOM_FORMULAS
from core.state import client_names

user_step = {}
user_data = {}
user_choice = {}
products = {}
user_mode = {}
last_messages = {}

# ================== PRODUCT ==================
def add_product(user_id, name, qty):
    products.setdefault(user_id, {})
    products[user_id][name] = products[user_id].get(name, 0) + qty


# ================== HISOB ==================
def hisobla(user_id):
    result = {}

    # 🔥 1-BOSQICH: TRUBALAR (faqat jihozlardan)
    for fiting, rule in HAMMOM_FORMULAS.items():

        # 👉 faqat truba formulalarini ajratamiz
        if "Truba" not in fiting:
            continue

        total = 0

        for product, count in rule.items():
            value = products[user_id].get(product, 0)

            if not isinstance(value, (int, float)) or value == 0:
                continue

            total += value * count

        if total > 0:
            result[fiting] = round(total)


    # 🔥 2-BOSQICH: QOLGAN HAMMASI (trubadan foydalanadi)
    for fiting, rule in HAMMOM_FORMULAS.items():

        # 👉 trubalarni skip qilamiz
        if "Truba" in fiting:
            continue

        total = 0

        for product, count in rule.items():

            # 🔥 ENG MUHIM QATOR
            value = (
                products[user_id].get(product, 0)
                or result.get(product, 0)
            )

            if not isinstance(value, (int, float)) or value == 0:
                continue

            total += value * count

        if total > 0:
            result[fiting] = round(total)

        for name, qty in products[user_id].items():

            if "Trap" in name:
                result[name] = qty

    return result

def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔄 Yangi hisob")
    markup.row("⬅️ Bosh menyu")
    return markup

# ================== START ==================
def start(user_id, bot):

    user_step[user_id] = "client_name"

    user_mode[user_id] = None
    user_choice[user_id] = None
    products[user_id] = {}

    bot.send_message(
        user_id,
        "👤 Mijoz ismini kiriting:",reply_markup=types.ReplyKeyboardRemove()
    )


# ================== HANDLE ==================
def handle(message, bot):
    user_id = message.chat.id
    text = message.text.strip()
    step = user_step.get(user_id)

    # 🔥 GLOBAL MENU BLOCK
    if text in ["🚿 Hammom hisoblash", "🔥 Isitish tizimi", "⬅️ Bosh menyu", "🔄 Yangi hisob"]:
        return

    step = user_step.get(user_id)


    if step == "start":
        start(user_id, bot)
        return

    # ---------- CLIENT NAME ----------
    if step == "client_name":

        client_names[user_id] = text

        user_step[user_id] = "mode"

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.add(
            "🏠 Hovli uy",
            "🏢 Honadon"
        )

        bot.send_message(
            user_id,
            "Hisoblash turini tanlang:",
            reply_markup=markup
        )

        return

    # ---------- MODE ----------
    if step == "mode":
        if "Hovli" in text:
            user_mode[user_id] = "hovli"
        elif "Honadon" in text:
            user_mode[user_id] = "honadon"
        else:
            bot.send_message(user_id, "❌ Iltimos tugmani tanlang")
            return

        user_step[user_id] = "uzunlik"
        bot.send_message(user_id, "📏 Hammom uzunligini kiriting:")
        return

    # ---------- UZUNLIK ----------
    elif step == "uzunlik":
        try:
            products[user_id]["Uzunlik"] = float(text)
        except:
            bot.send_message(user_id, "❌ Iltimos raqam kiriting")
            return

        user_step[user_id] = "kenglik"
        bot.send_message(user_id, "📏 Hammom kengligini kiriting:")
        return


    # ---------- KENGLIK ----------
    elif step == "kenglik":
        try:
            products[user_id]["Kenglik"] = float(text)
        except:
            bot.send_message(user_id, "❌ Iltimos raqam kiriting")
            return

        # 🔥 O‘lchamlarni olamiz
        uzunlik = products[user_id].get("Uzunlik", 0)
        kenglik = products[user_id].get("Kenglik", 0)

        # 🔥 Pol maydon hisoblash
        if uzunlik > 0 and kenglik > 0:
            products[user_id]["Pol maydon"] = uzunlik * kenglik

        # 🔽 KEYINGI STEP
        if user_mode[user_id] == "hovli":
            user_step[user_id] = "yomkist"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("350l", "500l", "650l", "750l", "1000l", "Yo'q")
            bot.send_message(user_id, "🛢 Yomkist turini tanlang:", reply_markup=markup)
        else:
            user_step[user_id] = "boiler"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("30l", "50l", "80l", "100l", "Yo'q")
            bot.send_message(user_id, "⚡️ Suv isitgich turini tanlang:", reply_markup=markup)

        return

    # ---------- YOMKIST ----------
    elif step == "yomkist":
        if text != "Yo'q":
            products[user_id][f"Yomkist {text}"] = 1

        user_step[user_id] = "boiler"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("30l", "50l", "80l", "100l", "Yo'q")
        bot.send_message(user_id, "⚡️ Suv isitgich turini tanlang:", reply_markup=markup)
        return

    # ---------- BOILER ----------
    elif step == "boiler":
        if text != "Yo'q":
            products[user_id][f"Boiler {text}"] = 1
        user_step[user_id] = "vanna"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Ha 1", "Ha 2", "Yo'q")

        bot.send_message(user_id, "🛁 Vanna qo'yamizmi?", reply_markup=markup)
        return

    # ---------- VANNA ----------
    elif step == "vanna":
        if "Ha" in text:
            add_product(user_id, "Vanna", 2 if "2" in text else 1)
            add_product(user_id, "Trap 10×10", 1)
        else:
            add_product(user_id, "Trap 10×40", 1)

        user_step[user_id] = "dush"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Ha 1", "Ha 2", "Yo'q")
        bot.send_message(user_id, "🚿 Dush smesitel qo'yamizmi?", reply_markup=markup)
        return

    # ---------- DUSH ----------
    elif step == "dush":
        if "Ha" in text:
            add_product(user_id, "Dush stayak", 2 if "2" in text else 1)

        user_step[user_id] = "rakvina"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Ha 1", "Ha 2", "Yo'q")
        bot.send_message(user_id, "🛀 Rakvina qo'yamizmi?", reply_markup=markup)
        return

    # ---------- RAKVINA ----------
    elif step == "rakvina":
        if "Ha" in text:
            add_product(user_id, "Rakvina", 2 if "2" in text else 1)

        user_step[user_id] = "unitaz"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        if user_mode[user_id] == "hovli":
            markup.add("Unitaz 1 ta", "Chashagen 1 ta")
            markup.add("Unitaz 2 ta", "Chashagen 2 ta")

            markup.add("Unitaz + Chashagen 1 tadan")
            markup.add("Unitaz + Chashagen 2 tadan")

            markup.add("Yo'q")
        else:
            markup.add("Unitaz 1", "Unitaz 2", "Yo'q")

        bot.send_message(user_id, "🚽 Unitaz sonini tanlang:", reply_markup=markup)
        return

    # ---------- UNITAZ ----------
    elif step == "unitaz":

        user_data.setdefault(user_id, {})

        unitaz_soni = 0

        if text == "Yo'q":
            pass
        else:
            qty = 2 if "2" in text else 1

            if "Unitaz" in text:
                add_product(user_id, "Unitaz", qty)
                unitaz_soni += qty

            if "Chashagen" in text:
                add_product(user_id, "Chashagen", qty)
                unitaz_soni += qty

        # 🔥 AGAR YO‘Q BO‘LSA → MUSTAHABNI SKIP
        if unitaz_soni == 0:
            if user_mode[user_id] == "hovli":
                user_step[user_id] = "taxorat"
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add("Ha 1", "Ha 2", "Yo'q")
                bot.send_message(user_id, "💧 Taxoratar uchun joy qo'yamizmi?", reply_markup=markup)
            else:
                user_step[user_id] = "kirmashina"
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add("Ha 1", "Ha 2", "Yo'q")
                bot.send_message(user_id, "🧺 Kir mashina uchun joy qoldiramizmi?", reply_markup=markup)
            return

        # 🔥 AGAR BOR BO‘LSA → MUSTAHABGA O‘T
        user_data[user_id]["unitaz_total"] = unitaz_soni

        user_step[user_id] = "mustahab"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Ha", "Yo'q")

        bot.send_message(user_id,"🔧 Unitazga mustahab smesitel qo'yamizmi?", reply_markup=markup)
        return

    # ---------- MUSTAHAB ----------
    elif step == "mustahab":

        if text == "Ha":
            qty = user_data[user_id].get("unitaz_total", 1)
            add_product(user_id, "Mustahab smesitel", qty)

        # 🔥 KEYINGI STEP
        if user_mode[user_id] == "hovli":
            user_step[user_id] = "taxorat"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Ha 1", "Ha 2", "Yo'q")
            bot.send_message(user_id, "💧 Taxorat uchun joy qo'yamizmi?:", reply_markup=markup)
        else:
            user_step[user_id] = "kirmashina"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Ha 1", "Ha 2", "Yo'q")
            bot.send_message(user_id, "🧺 Kir mashina uchun joy qoldiramizmi?", reply_markup=markup)

        return

    # ---------- TAXORAT ----------
    elif step == "taxorat":
        if "Ha" in text:
            add_product(user_id, "Taxorat smesitel", 2 if "2" in text else 1)

        user_step[user_id] = "kirmashina"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Ha 1", "Ha 2", "Yo'q")
        bot.send_message(user_id, "🧺 Kir mashina uchun joy qoldiramizmi?", reply_markup=markup)
        return

    # ---------- KIR MASHINA ----------
    elif step == "kirmashina":
        if "Ha" in text:
            add_product(user_id, "Kirmashina", 2 if "2" in text else 1)

        # 🔥 KEYINGI STEP → SUSHILKA
        user_step[user_id] = "sushilka"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Ha", "Yo'q")

        bot.send_message(user_id, "♨️ Sushilka qo‘yilsinmi?", reply_markup=markup)
        return

    # ---------- SUSHILKA ----------
    elif step == "sushilka":

        if text == "Ha":
            add_product(user_id, "Sushilka", 1)

            # 🔥 FITTINGLAR
            add_product(user_id, "Sushilka kran", 2)

        elif text == "Yo'q":
            pass
        else:
            bot.send_message(user_id, "❌ Iltimos tugma tanlang")
            return

        # 🔥 KEYINGI → ISITISH (POL)
        user_step[user_id] = "isitish"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Suvlik pol",
                   "Kabellik pol",
                            "Yo'q")

        bot.send_message(user_id, "🔥 Isitish turini tanlang:", reply_markup=markup)
        return

    # ---------- ISITISH ----------
    elif step == "isitish":

        pol = products[user_id].get("Pol maydon", 0)

        # ================= SUVLIK POL =================
        if text == "Suvlik pol" and pol > 0:

            truba = round(pol * 7)
            add_product(user_id, "Truba 16 (folgasiz)", truba)

            add_product(user_id, "Penaplast", round(pol * 1.4))
            add_product(user_id, "Gidropara (folga)", round(pol))
            add_product(user_id, "Skoba", truba * 3)

            kontur = math.ceil(truba / 70)

            if kontur > 0:
                add_product(user_id, f"Kollektor {kontur} kontur", 1)
                add_product(user_id, "Nasos 25.4.180", 1)
                add_product(user_id, "Kollektor smesitel", 1)

        # ================= KABELLIK POL =================
        elif text == "Kabellik pol" and pol > 0:

            kabel = round(pol * 6)
            add_product(user_id, "Isitish kabeli", kabel)

            add_product(user_id, "Toklipol Datchik", 1)

            add_product(user_id, "Penaplast", round(pol * 1.2))
            add_product(user_id, "Gidropara (folga)", round(pol))

        elif text == "Yo'q":
            pass

        else:
            bot.send_message(user_id, "❌ Iltimos tugma tanlang")
            return

        # 🔥 HISOB
        result = hisobla(user_id)

        # 🔥 ENGINE (hammasini qiladi)
        text = process(user_id, result, products)

        # 🔥 SEND NEW SMETA
        bot.send_message(
            user_id,
            text
        )

        data = {
            "materials": result,
            "equipment": products[user_id].copy()
        }

        # 🔥 RESET
        products[user_id] = {}

        # 🔥 MENU
        bot.send_message(user_id, "Tanlang:", reply_markup=main_menu_keyboard())

        # 🔥 RESET STEP
        user_step[user_id] = "start"

        return data
