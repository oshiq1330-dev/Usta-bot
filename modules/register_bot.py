from telebot import types

user_data = {}
user_step = {}


# ================== TEXT NORMALIZE ==================
def normalize(text):
    return (text or "").strip().lower().replace("‘", "'").replace("’", "'").replace("`", "'")


# ================== KEYBOARDS ==================
def role_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("👷 Usta", "🏪 Do'konchi")
    markup.row("👤 Mijoz")
    return markup


def phone_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(
            "📞 Telefon yuborish",
            request_contact=True
        )
    )
    return markup


def location_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(
            "📍 Lokatsiya yuborish",
            request_location=True
        )
    )
    return markup


# ================== START ==================
def start(user_id, bot):

    user_data.pop(user_id, None)

    user_step[user_id] = "choose_role"

    bot.send_message(
        user_id,
        "👋 Xush kelibsiz!\n\nSiz kimsiz?",
        reply_markup=role_keyboard()
    )


# ================== PHONE EXTRACT ==================
def extract_phone(message):

    # 📞 CONTACT
    if getattr(message, "contact", None):
        if message.contact.phone_number:
            return message.contact.phone_number.strip()

    # ✍️ TEXT
    text = (message.text or "").strip()

    digits = "".join(
        ch for ch in text
        if ch.isdigit() or ch == "+"
    )

    if len(digits) >= 9:
        return digits

    return None


# ================== HANDLE ==================
def handle(message, bot, cursor, conn):

    user_id = message.chat.id

    step = user_step.get(user_id)

    text = (message.text or "").strip()

    norm = normalize(text)

    # ================== ROLE ==================
    if step == "choose_role":

        if "usta" in norm:
            role = "usta"

        elif "do'kon" in norm or "dokondor" in norm:
            role = "dokondor"

        elif "mijoz" in norm:
            role = "mijoz"

        else:
            bot.send_message(
                user_id,
                "❌ Tugmalardan tanlang",
                reply_markup=role_keyboard()
            )
            return False

        user_data[user_id] = {
            "role": role
        }

        user_step[user_id] = "get_name"

        bot.send_message(
            user_id,
            "👤 Ismingizni kiriting:",
            reply_markup=types.ReplyKeyboardRemove()
        )

        return False

    # ================== NAME ==================
    elif step == "get_name":

        if not text:
            bot.send_message(
                user_id,
                "❌ Ism kiriting"
            )
            return False

        user_data.setdefault(user_id, {})

        user_data[user_id]["name"] = text

        user_step[user_id] = "get_phone"

        bot.send_message(
            user_id,
            "📞 Telefon raqamingizni yuboring:",
            reply_markup=phone_keyboard()
        )

        return False

    # ================== PHONE ==================
    elif step == "get_phone":

        phone = extract_phone(message)

        if not phone:

            bot.send_message(
                user_id,
                "❌ Telefonni tugma orqali yuboring yoki yozing"
            )

            return False

        user_data.setdefault(user_id, {})

        user_data[user_id]["phone"] = phone

        user_step[user_id] = "get_location"

        bot.send_message(
            user_id,
            "📍 Lokatsiyangizni yuboring:",
            reply_markup=location_keyboard()
        )

        return False

    # ================== LOCATION ==================
    elif step == "get_location":

        if not getattr(message, "location", None):

            bot.send_message(
                user_id,
                "❌ Lokatsiyani tugma orqali yuboring"
            )

            return False

        lat = message.location.latitude
        lon = message.location.longitude

        data = user_data.get(user_id, {})

        role = data.get("role", "")
        name = data.get("name", "")
        phone = data.get("phone", "")

        # ================== SAVE DB ==================
        cursor.execute("""
            INSERT OR REPLACE INTO users
            (user_id, role, name, phone, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            role,
            name,
            phone,
            lat,
            lon
        ))

        conn.commit()

        # ================== CLEAN ==================
        user_step[user_id] = "done"

        user_data.pop(user_id, None)

        bot.send_message(
            user_id,
            "✅ Ro'yxatdan o'tdingiz!"
        )

        return True

    return False
