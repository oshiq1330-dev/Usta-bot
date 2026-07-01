import os
import telebot
import threading
import datetime
import time

from telebot import types

from utils import send_replace, delete_safe, last_message
from core.location import calculate_distance
from core.db import conn, cursor
from modules import register_bot, hammom_bot, isitish_bot
from core.nearby import find_nearby_masters
from core.shops import find_nearby_shops
from core.state import client_names
from core.estimate import calculate_estimate
from core.formatter import format_result

# 🔐 TOKEN
BOT_TOKEN = ("8712016631:AAFLBiNb0GF9G6DuckxPwx62Ci3aGTrl1xY")

bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_IDS = {5426288999}  # bu yerga o'zingning Telegram ID'ingni yoz
admin_broadcast_target = {}

user_mode = {}
user_request = {}
user_search_step = {}
shop_offer_step = {}
shop_offer_client = {}
estimate_offer_step = {}
estimate_offer_client = {}
active_orders = {}
last_messages = {}
request_messages = {}
accepted_requests = set()
delivery_step = {}
product_request_messages = {}
estimate_sales_check = {}

def auto_delete(chat_id, message_id):

    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass


# ================== MENU ==================
def show_main_menu(user_id):

    cursor.execute(
        "SELECT role FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    role = user[0] if user else None

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    # 👷 USTA
    if role == "usta":

        cursor.execute("""
            SELECT is_online
            FROM users
            WHERE user_id=?
        """, (user_id,))

        online = cursor.fetchone()[0]

        status_btn = (
            "🟢 Ishlayapman"
            if online == 1
            else "🔴 Ishlamayapman"
        )

        markup.row(status_btn)

        markup.row("🛒 Mahsulot kerak")

        markup.row(
            "🚿 Hammom hisoblash",
            "🔥 Isitish tizimi"
        )

        markup.row("⚙️ Lokatsiyani o'zgartirish")

        bot.send_message(
            user_id,
            "Kerakli bo‘limni tanlang:",
            reply_markup=markup
        )

    # 👤 MIJOZ
    elif role == "mijoz":

        markup.row("👷 Usta kerak")
        markup.row("⚙️ Lokatsiyani o'zgartirish")

        bot.send_message(
            user_id,
            "👋 Siz ustalarni qidirishingiz mumkin",
            reply_markup=markup
        )

    # 🏪 DO'KONCHI
    elif role == "dokondor":

        markup.row("👷 Ustalar")
        markup.row("📊 Statistika")
        markup.row("⚙️ Profil")

        bot.send_message(
            user_id,
            "🏪 Do‘kon paneliga xush kelibsiz",
            reply_markup=markup
        )


# ================== START ==================
@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.chat.id

    cursor.execute(
        "SELECT role, last_location_update FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    # 🔥 REGISTER
    if not user:

        register_bot.start(user_id, bot)
        return

    role, last_update = user

    # ================== USTA LOCATION CHECK ==================

    if role == "usta":

        from datetime import datetime, timedelta

        need_update = False

        # 🔥 FIRST TIME
        if not last_update:
            need_update = True

        else:

            try:

                last_time = datetime.fromisoformat(
                    last_update
                )

                if datetime.now() - last_time > timedelta(hours=24):
                    need_update = True

            except:
                need_update = True

        # 🔥 ASK LOCATION
        if need_update:

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            button = types.KeyboardButton(
                "📍 Lokatsiyani yangilash",
                request_location=True
            )

            markup.add(button)

            send_replace(
                bot,
                user_id,
                "📍 Lokatsiyangiz eskirgan\n\n"
                "Iltimos yangi lokatsiyani yuboring.",
                reply_markup=markup
            )

            user_search_step[user_id] = "update_location"

            return

    # ================== NORMAL MENU ==================

    user_mode[user_id] = None

    show_main_menu(user_id)

#-----admin panel------
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    user_id = message.chat.id

    if user_id not in ADMIN_IDS:
        return

    user_mode[user_id] = "admin"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📣 Xabar yuborish", "📊 Statistika")
    markup.row("👥 Foydalanuvchilar", "📦 Zakazlar")
    markup.row("⬅️ Bosh menyu")

    bot.send_message(
        user_id,
        "👑 Admin panel",
        reply_markup=markup
    )

# ================== MAIN HANDLER ==================
@bot.message_handler(content_types=["text", "contact", "location", "photo"])
def main_handler(message):

    user_id = message.chat.id

    text = (
        (message.text or "")
        .strip()
        .replace("‘", "'")
        .replace("’", "'")
        .replace("`", "'")
    )

    # ================== ADMIN PANEL ==================
    if user_id in ADMIN_IDS and user_mode.get(user_id) == "admin":

        # ⬅️ Bosh menyu
        if text == "⬅️ Bosh menyu":
            user_mode[user_id] = None
            admin_broadcast_target.pop(user_id, None)
            show_main_menu(user_id)
            return

        # 📣 Broadcast menyu
        if text == "📣 Xabar yuborish":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("👷 Ustalarga", "👤 Mijozlarga")
            markup.row("🏪 Do'konlarga", "❌ Bekor qilish")

            bot.send_message(
                user_id,
                "Qaysi guruhga yuboramiz?",
                reply_markup=markup
            )
            return

        if text == "👷 Ustalarga":
            admin_broadcast_target[user_id] = "usta"
            bot.send_message(
                user_id,
                "Ustalarga yuboriladigan xabarni yozing:"
            )
            return

        if text == "👤 Mijozlarga":
            admin_broadcast_target[user_id] = "mijoz"
            bot.send_message(
                user_id,
                "Mijozlarga yuboriladigan xabarni yozing:"
            )
            return

        if text == "🏪 Do'konlarga":
            admin_broadcast_target[user_id] = "dokondor"
            bot.send_message(
                user_id,
                "Do'konlarga yuboriladigan xabarni yozing:"
            )
            return

        if text == "❌ Bekor qilish":


            admin_broadcast_target.pop(user_id, None)

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            markup.row(
                "📣 Xabar yuborish",
                "📊 Statistika"
            )

            markup.row(
                "👥 Foydalanuvchilar",
                "📦 Zakazlar"
            )

            markup.row(
                "⬅️ Bosh menyu"
            )

            bot.send_message(
                user_id,
                "👑 Admin panel",
                reply_markup=markup
            )

            return

        # 📣 Xabar yuborish bosqichi
        if user_id in admin_broadcast_target:
            target_role = admin_broadcast_target.pop(user_id)

            cursor.execute("""
                SELECT user_id
                FROM users
                WHERE role=?
            """, (target_role,))
            rows = cursor.fetchall()

            sent = 0
            failed = 0

            for row in rows:
                uid = row[0]
                try:
                    bot.send_message(uid, text)
                    sent += 1
                except:
                    failed += 1

            bot.send_message(
                user_id,
                f"✅ Yuborildi\n\n"
                f"📨 Yetib bordi: {sent}\n"
                f"⚠️ Xatolik: {failed}"
            )
            return

        # 📊 Statistika
        if text == "📊 Statistika":
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE role='usta'")
            masters = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE role='dokondor'")
            shops = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE role='mijoz'")
            clients = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM requests")
            requests_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM product_requests")
            product_requests_count = cursor.fetchone()[0]

            bot.send_message(
                user_id,
                f"📊 Statistika\n\n"
                f"👥 Jami foydalanuvchilar: {total_users}\n"
                f"👷 Ustalar: {masters}\n"
                f"🏪 Do‘konchilar: {shops}\n"
                f"👤 Mijozlar: {clients}\n"
                f"🛠 Usta zakazlari: {requests_count}\n"
                f"🛒 Mahsulot so‘rovlari: {product_requests_count}"
            )
            return

        if text == "👥 Foydalanuvchilar":

            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM users
                WHERE is_online=1 AND role='usta'
            """)
            online_masters = cursor.fetchone()[0]

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            markup.row(
                "👷 Ustalar",
                "🏪 Do'konlar"
            )

            markup.row(
                "👤 Mijozlar"
            )

            markup.row("🔙 Orqaga")

            bot.send_message(
                user_id,
                f"👥 Foydalanuvchilar\n\n"
                f"Jami: {total_users}\n"
                f"🟢 Online ustalar: {online_masters}\n\n"
                f"Kerakli bo'limni tanlang:",
                reply_markup=markup
            )

            return

        if text == "📦 Zakazlar":
            cursor.execute("SELECT COUNT(*) FROM requests")
            service_requests = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM product_requests")
            product_requests_count = cursor.fetchone()[0]

            bot.send_message(
                user_id,
                f"📦 Zakazlar\n\n"
                f"🛠 Servis zakazlari: {service_requests}\n"
                f"🛒 Mahsulot so‘rovlari: {product_requests_count}"
            )
            return

        if text == "🔄 Yangilash":
            bot.send_message(user_id, "✅ Yangilandi")
            return

        if text == "👷 Ustalar":

            cursor.execute("""
                SELECT name, phone
                FROM users
                WHERE role='usta'
                ORDER BY name
            """)

            rows = cursor.fetchall()

            if not rows:
                bot.send_message(
                    user_id,
                    "👷 Ustalar topilmadi"
                )
                return

            text_send = f"👷 Ustalar ({len(rows)} ta)\n\n"

            for i, (name, phone) in enumerate(rows, start=1):

                text_send += (
                    f"{i}. {name}\n"
                    f"📞 {phone}\n\n"
                )

            bot.send_message(
                user_id,
                text_send
            )

            return

        if text == "🏪 Do'konlar":

            cursor.execute("""
                SELECT name, phone
                FROM users
                WHERE role='dokondor'
                ORDER BY name
            """)

            rows = cursor.fetchall()

            if not rows:
                bot.send_message(
                    user_id,
                    "🏪 Do'konlar topilmadi"
                )
                return

            text_send = f"🏪 Do'konlar ({len(rows)} ta)\n\n"

            for i, (name, phone) in enumerate(rows, start=1):

                text_send += (
                    f"{i}. {name}\n"
                    f"📞 {phone}\n\n"
                )

            bot.send_message(
                user_id,
                text_send
            )

            return

        if text == "👤 Mijozlar":

            cursor.execute("""
                SELECT name, phone
                FROM users
                WHERE role='mijoz'
                ORDER BY name
            """)

            rows = cursor.fetchall()

            if not rows:
                bot.send_message(
                    user_id,
                    "👤 Mijozlar topilmadi"
                )
                return

            text_send = f"👤 Mijozlar ({len(rows)} ta)\n\n"

            for i, (name, phone) in enumerate(rows, start=1):

                text_send += (
                    f"{i}. {name}\n"
                    f"📞 {phone}\n\n"
                )

            bot.send_message(
                user_id,
                text_send
            )

            return

        if text == "🔙 Orqaga":

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

            markup.row("📊 Statistika", "👥 Foydalanuvchilar")
            markup.row("📦 Zakazlar", "📣 Xabar yuborish")
            markup.row("🔄 Yangilash")

            bot.send_message(
                user_id,
                "🔧 Admin panel",
                reply_markup=markup
            )

            return

#___
    if user_id in delivery_step:

        if not message.location:
            bot.send_message(
                user_id,
                "❌ Lokatsiyani tugma orqali yuboring"
            )
            return

        lat = message.location.latitude
        lon = message.location.longitude

        requester_id = delivery_step[user_id]["requester_id"]
        shop_id = delivery_step[user_id]["shop_id"]

        cursor.execute("""
            SELECT name, phone
            FROM users
            WHERE user_id=?
        """, (requester_id,))
        requester = cursor.fetchone()

        cursor.execute("""
            SELECT name, phone
            FROM users
            WHERE user_id=?
        """, (shop_id,))
        shop = cursor.fetchone()

        if requester and shop:
            requester_name, requester_phone = requester
            shop_name, shop_phone = shop

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "📦 Yubordim",
                    callback_data=f"sent_{requester_id}_{shop_id}"
                )
            )

            bot.send_message(
                shop_id,
                f"🚕 Yetkazib berish\n\n"
                f"👤 Mijoz: {requester_name}\n"
                f"📞 {requester_phone}\n\n"
                f"📍 Lokatsiya yuborildi",
                reply_markup=markup
            )

            bot.send_location(shop_id, lat, lon)

            bot.send_message(
                user_id,
                "✅ Lokatsiya do‘konga yuborildi",
                reply_markup=types.ReplyKeyboardRemove()
            )

        delivery_step.pop(user_id, None)
        show_main_menu(user_id)
        return

    if text == "👷 Usta kerak":
        user_search_step.pop(user_id, None)

    # ================== NEARBY MASTERS FOR SHOP ==================

    if text == "👷 Ustalar":

        user_search_step.pop(user_id, None)

        cursor.execute("""
            SELECT lat, lon
            FROM users
            WHERE user_id=?
        """, (user_id,))

        row = cursor.fetchone()

        if not row:
            bot.send_message(user_id, "❌ Lokatsiya topilmadi")
            return

        lat, lon = row

        masters = find_nearby_masters(
            cursor,
            lat,
            lon,
            radius=10
        )

        if not masters:
            bot.send_message(user_id, "❌ Yaqin atrofda ustalar topilmadi")
            return

        text_result = "👷 Yaqin ustalar:\n\n"

        for master in masters[:10]:
            text_result += (
                f"👤 {master['name']}\n"
                f"⭐ {master['rating']:.1f}\n"
                f"📞 {master['phone']}\n"
                f"📍 {master['distance']} km\n\n"
            )

        bot.send_message(user_id, text_result)
        return

    # ================== SHOP STAT ==================

    if text == "📊 Statistika":

        cursor.execute("""
            SELECT shop_rating, shop_sales
            FROM users
            WHERE user_id=?
        """, (user_id,))

        row = cursor.fetchone()

        if not row:
            bot.send_message(user_id, "❌ Ma'lumot topilmadi")
            return

        shop_rating, shop_sales = row

        bot.send_message(
            user_id,
            f"📊 Do‘kon statistikasi\n\n"
            f"⭐ Reyting: {shop_rating:.1f}\n"
            f"📦 Sotuvlar: {shop_sales} ta"
        )
        return

    if text == "⚙️ Profil":
        user_search_step.pop(user_id, None)

        cursor.execute("""
            SELECT name, phone, shop_rating, shop_sales
            FROM users
            WHERE user_id=?
        """, (user_id,))

        row = cursor.fetchone()

        if not row:
            bot.send_message(user_id, "❌ Profil topilmadi")
            return

        name, phone, shop_rating, shop_sales = row

        bot.send_message(
            user_id,
            f"🏪 Do‘kon profili\n\n"
            f"👤 {name}\n"
            f"📞 {phone}\n"
            f"⭐ Reyting: {shop_rating:.1f}\n"
            f"📦 Sotuvlar: {shop_sales} ta"
        )
        return

    # ================== ONLINE / OFFLINE ==================

    if text == "🟢 Ishlayapman":

        cursor.execute("""
            UPDATE users
            SET is_online=0
            WHERE user_id=?
        """, (user_id,))

        conn.commit()

        bot.send_message(
            user_id,
            "🔴 Siz offlinedasiz"
        )

        user_search_step.pop(user_id, None)
        show_main_menu(user_id)

        return


    if text == "🔴 Ishlamayapman":

        cursor.execute("""
            UPDATE users
            SET is_online=1
            WHERE user_id=?
        """, (user_id,))

        conn.commit()

        # 🔥 ISH TUGADI -> MIJOZGA RATING
        if user_id in active_orders.values():

            cursor.execute("""
                SELECT
                    name,
                    phone,
                    rating,
                    completed_jobs
                FROM users
                WHERE user_id=?
            """, (user_id,))

            master_info = cursor.fetchone()

            if master_info:
                master_name, master_phone, master_rating, completed_jobs = master_info
            else:
                master_name = "Noma'lum"
                master_phone = "-"
                master_rating = 0
                completed_jobs = 0

            for client_id, master_id in list(active_orders.items()):

                if master_id == user_id:

                    markup = types.InlineKeyboardMarkup()

                    for i in range(1, 6):

                        markup.add(
                            types.InlineKeyboardButton(
                                f"⭐ {i}",
                                callback_data=f"rate_{user_id}_{i}"
                            )
                        )

                    bot.send_message(
                        client_id,
                        "⭐ Usta ishini baholang:"
                        f"👷 Usta: {master_name}\n"
                        f"📞 {master_phone}\n"
                        f"⭐ Reytingi: {master_rating:.1f}\n"
                        f"🛠 Bajarilgan ishlar: {completed_jobs} ta",

                        reply_markup=markup
                    )

                    active_orders.pop(client_id, None)

                    if client_id in accepted_requests:

                        accepted_requests.remove(client_id)

        bot.send_message(
            user_id,
            "🟢 Siz online bo‘ldingiz"
        )

        user_search_step.pop(user_id, None)
        show_main_menu(user_id)

        return

    # ================== ESTIMATE OFFER TEXT ==================

    if estimate_offer_step.get(user_id) == "waiting_offer":

        client_id = estimate_offer_client.get(user_id)

        cursor.execute("""
            SELECT
                name,
                phone,
                shop_rating,
                shop_sales
            FROM users
            WHERE user_id=?
        """, (user_id,))

        shop = cursor.fetchone()

        if shop:

            name, phone, shop_rating, shop_sales = shop

            send_text = (
                "📦 SMETA TAKLIFI\n\n"
                f"🏪 {name}\n"
                f"⭐ Reyting: {shop_rating:.1f}\n"
                f"📦 Savdolar: {shop_sales} ta\n"
                f"📞 {phone}\n\n"
                f"💰 Taklif narxi: {text} so'm"
            )

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "✅ Qabul qilish",
                    callback_data=f"estimate_accept_{client_id}_{user_id}"
                )
            )

            bot.send_message(
                client_id,
                send_text,
                reply_markup=markup
            )

        bot.send_message(
            user_id,
            "✅ Smeta taklifi yuborildi"
        )

        estimate_offer_step.pop(user_id, None)
        estimate_offer_client.pop(user_id, None)

        return

    # ================== SHOP OFFER TEXT ==================

    if shop_offer_step.get(user_id) == "waiting_offer":

        client_id = shop_offer_client.get(user_id)

        cursor.execute("""
            SELECT
                name,
                phone,
                shop_rating,
                shop_sales
            FROM users
            WHERE user_id=?
        """, (user_id,))

        shop = cursor.fetchone()

        if shop:

            name, phone, shop_rating, shop_sales = shop
            product_name = user_request.get(user_id, {}).get("product_name", "Mahsulot")

            send_text = (
                 "🏪 DO‘KON TAKLIFI\n\n"
                f"🏪 {name}\n"
                f"⭐ Reyting: {shop_rating:.1f}\n"
                f"📦 Savdolar: {shop_sales} ta\n"
                f"📞 {phone}\n\n"
                f"🔧 Mahsulot: {product_name}\n"
                f"💰 Narxi: {text} so‘m"
            )

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🚕 Yetkazib berish",
                    callback_data=f"delivery_{client_id}_{user_id}"
                )
            )

            # 🔥 SAVE PRODUCT REQUEST
            cursor.execute("""
                INSERT INTO product_requests (
                    master_id,
                    shop_id,
                    product_name,
                    price,
                    status
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                client_id,
                user_id,
                product_name,
                text,
                "offered"
            ))

            conn.commit()

            bot.send_message(
                client_id,
                send_text,
                reply_markup=markup
            )

        bot.send_message(
            user_id,
            "✅ Taklif yuborildi"
        )

        shop_offer_step.pop(user_id, None)
        shop_offer_client.pop(user_id, None)

        return

    # ================== REGISTER CHECK ==================
    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:

        done = register_bot.handle(
            message,
            bot,
            cursor,
            conn
        )

        if done:
            user_mode[user_id] = None
            show_main_menu(user_id)

        return

    # ================== INIT USER ==================
    if user_id not in user_mode:
        user_mode[user_id] = None
        show_main_menu(user_id)
        return

    if text == "⚙️ Lokatsiyani o'zgartirish":

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        button = types.KeyboardButton(
            "📍 Lokatsiyani yuborish",
            request_location=True
        )

        markup.add(button)

        bot.send_message(
            user_id,
            "📍 Yangi lokatsiyangizni yuboring",
            reply_markup=markup
        )

        user_search_step[user_id] = "update_location"

        return

    # ================== PRODUCT REQUEST ==================

    if text == "🛒 Mahsulot kerak":

        user_search_step[user_id] = "waiting_product_name"

        bot.send_message(
            user_id,
            "🛒 Kerakli mahsulot nomini yozing"
        )

        return

    # ================== USTA KERAK ==================

    if text == "👷 Usta kerak":

        if user_id in active_orders:

            markup = types.InlineKeyboardMarkup()

            markup.row(
                types.InlineKeyboardButton(
                    "✅ Ha",
                    callback_data=f"cancel_order_yes_{user_id}"
                ),
                types.InlineKeyboardButton(
                    "❌ Yo'q",
                    callback_data=f"cancel_order_no_{user_id}"
                )
            )

            bot.send_message(
                user_id,
                "⚠️ Sizda faol buyurtma mavjud.\n\n"
                "Yangi usta qidirish uchun eski buyurtmani bekor qilasizmi?",
                reply_markup=markup
            )

            return

        user_search_step[user_id] = "waiting_problem"

        bot.send_message(
            user_id,
            "🛠 Muammoni yozing\n\n"
            "Masalan:\n"
            "• Nasos ishlamayapti\n"
            "• Ariston tozalash kerak\n"
            "• Unitaz oqyapti"
        )

        return

    # ================== LOCATION SETTINGS ==================

    if text == "⚙️ Lokatsiyani o'zgartirish":

        user_search_step[user_id] = "change_location"

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.add(
            types.KeyboardButton(
                "📍 Yangi lokatsiya yuborish",
                request_location=True
            )
        )

        bot.send_message(
            user_id,
            "📍 Yangi asosiy lokatsiyani yuboring",
            reply_markup=markup
        )

        return

    # ================== MUAMMO QABUL ==================

    if user_search_step.get(user_id) == "waiting_problem":

        user_request[user_id] = {
            "problem": text
        }

        user_search_step[user_id] = "confirm_location"

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.row("✅ Ha", "📍 Boshqa joy")

        bot.send_message(
            user_id,
            "📍 Muammo eski adresdami?",
            reply_markup=markup
        )

        return

    # ================== PRODUCT PHOTO ==================

    if user_search_step.get(user_id) == "waiting_product_photo":

        if message.text == "⏭ Surat yo'q":

            product_name = user_request[user_id]["product_name"]

            user_search_step.pop(user_id, None)

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "✅ Menda bor",
                    callback_data=f"shop_have_{user_id}"
                )
            )

            cursor.execute("""
                SELECT user_id
                FROM users
                WHERE role='dokondor'
            """)

            shops = cursor.fetchall()

            for shop in shops:

                shop_id = shop[0]

                try:

                    msg = bot.send_message(
                        shop_id,
                        "🛒 Yangi mahsulot so‘rovi\n\n"
                        f"🔧 {product_name}\n\n"
                        "📷 Surat mavjud emas",
                        reply_markup=markup
                    )

                    product_request_messages.setdefault(
                        user_id,
                        []
                    ).append(
                       (shop_id, msg.message_id)
                    )

                except:
                    pass

            bot.send_message(
                user_id,
                "✅ So‘rov do‘konlarga yuborildi"
            )

            show_main_menu(user_id)

            return

        if not message.photo:

            bot.send_message(
                user_id,
                "❌ Mahsulot rasmini yuboring yoki '⏭ Surat yo'q' tugmasini bosing"
            )

            return


        product_name = user_request[user_id]["product_name"]

        photo_id = message.photo[-1].file_id

        user_search_step.pop(user_id, None)

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "✅ Menda bor",
                callback_data=f"shop_have_{user_id}"
            )
        )

        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE role='dokondor'
        """)

        shops = cursor.fetchall()

        for shop in shops:

            shop_id = shop[0]

            try:

                msg = bot.send_photo(
                    shop_id,
                    photo_id,
                    caption=(
                        "🛒 Yangi mahsulot so‘rovi\n\n"
                        f"🔧 {product_name}"
                    ),
                    reply_markup=markup
                )

                product_request_messages.setdefault(
                    user_id,
                    []
                ).append(
                    (shop_id, msg.message_id)
                )

            except Exception as e:
                print("PHOTO ERROR:", e)

        bot.send_message(
            user_id,
            "✅ So‘rov do‘konlarga yuborildi"

        )

        show_main_menu(user_id)

        return

    # ================== PRODUCT NAME ==================

    if user_search_step.get(user_id) == "waiting_product_name":

        user_request.setdefault(user_id, {})
        user_request[user_id]["product_name"] = text

        user_search_step[user_id] = "waiting_product_photo"

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.add("⏭ Surat yo'q")

        bot.send_message(
            user_id,
            "📷 Mahsulot rasmini yuboring yoki o'tkazib yuboring",
            reply_markup=markup
        )

        user_search_step[user_id] = "waiting_product_photo"

        return

    # ================== CHANGE CLIENT LOCATION ==================

    if user_search_step.get(user_id) == "change_location":

        if not message.location:

            bot.send_message(
                user_id,
                "❌ Lokatsiyani tugma orqali yuboring"
            )

            return

        lat = message.location.latitude
        lon = message.location.longitude

        cursor.execute("""
            UPDATE users
            SET lat=?,
                lon=?
            WHERE user_id=?
        """, (
            lat,
            lon,
            user_id
        ))

        conn.commit()

        user_search_step.pop(user_id, None)

        bot.send_message(
            user_id,
            "✅ Asosiy lokatsiya yangilandi"
        )

        show_main_menu(user_id)

        return

    # ================== UPDATE MASTER LOCATION ==================

    if user_search_step.get(user_id) == "update_location":

        if not message.location:

            bot.send_message(
                user_id,
                "❌ Lokatsiyani tugma orqali yuboring"
            )

            return

        lat = message.location.latitude
        lon = message.location.longitude

        now = datetime.datetime.now().isoformat()

        # 🔥 UPDATE LOCATION
        cursor.execute("""
            UPDATE users
            SET lat=?,
                lon=?,
                last_location_update=?
            WHERE user_id=?
        """, (
            lat,
            lon,
            now,
            user_id
        ))

        conn.commit()

        user_search_step.pop(user_id, None)

        bot.send_message(
            user_id,
            "✅ Lokatsiya yangilandi"
        )

        user_mode[user_id] = None

        show_main_menu(user_id)

        return

    # ================== ESKI LOKATSIYA ==================

    if (
        user_search_step.get(user_id) == "confirm_location"
        and text == "✅ Ha"
    ):

        cursor.execute("""
            SELECT lat, lon
            FROM users
            WHERE user_id=?
        """, (user_id,))

        row = cursor.fetchone()

        if not row:
            bot.send_message(
                user_id,
                "❌ Lokatsiya topilmadi"
            )
            return

        lat, lon = row

        problem = user_request[user_id]["problem"]

        user_search_step[user_id] = "waiting_location"

        class FakeLocation:
            latitude = lat
            longitude = lon

        message.location = FakeLocation()

    # ================== YANGI LOKATSIYA ==================

    if (
        user_search_step.get(user_id) == "confirm_location"
        and text == "📍 Boshqa joy"
    ):

        user_search_step[user_id] = "waiting_location"

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.add(
            types.KeyboardButton(
                "📍 Lokatsiya yuborish",
                request_location=True
            )
        )

        bot.send_message(
            user_id,
            "📍 Yangi lokatsiyani yuboring",
            reply_markup=markup
        )

        return

    # ================== LOCATION QABUL ==================

    if user_search_step.get(user_id) == "waiting_location":

        if not message.location:

            bot.send_message(
                user_id,
                "❌ Lokatsiyani tugma orqali yuboring"
            )

            return

        lat = message.location.latitude
        lon = message.location.longitude

        problem = user_request[user_id]["problem"]

        user_search_step[user_id] = "waiting_location"

        # ================== REQUEST SAVE ==================

        cursor.execute("""
            INSERT INTO requests (
                client_id,
                problem,
                lat,
                lon
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            problem,
            lat,
            lon
        ))

        conn.commit()

        # ================== NEARBY MASTERS ==================

        masters = find_nearby_masters(
            cursor,
            lat,
            lon,
            radius=10
        )

        if not masters:

            bot.send_message(
                user_id,
                "❌ Yaqin atrofda ustalar topilmadi"
            )

            user_search_step.pop(user_id, None)

            show_main_menu(user_id)

            return

        # ================== SEND TO MASTERS ==================

        for master in masters:

            try:

                text_send = (
                    "📥 Yangi mijoz so‘rovi\n\n"
                    f"🛠 Muammo:\n{problem}\n\n"
                    f"📍 Masofa: {master['distance']} km"
                )

                markup = types.InlineKeyboardMarkup()

                markup.add(
                    types.InlineKeyboardButton(
                        "✅ Qabul qilish",
                        callback_data=f"accept_{user_id}"
                    )
                )

                msg = bot.send_message(
                    master["user_id"],
                    text_send,
                    reply_markup=markup
                )

                # 🔥 AUTO DELETE
                threading.Timer(
                    300,
                    auto_delete,
                    args=(
                        master["user_id"],
                        msg.message_id
                    )
                ).start()

                # 🔥 REQUEST SAVE
                if user_id not in request_messages:
                    request_messages[user_id] = []

                request_messages[user_id].append(
                    (
                        master["user_id"],
                        msg.message_id
                    )
                )

            except:
                pass

        # 🔥 RESET SEARCH STEP
        user_search_step.pop(user_id, None)

        # 🔥 MAIN MENU
        show_main_menu(user_id)

        # ================== CLIENT MESSAGE ==================

        text_result = (
            "✅ So‘rovingiz yaqin ustalarga yuborildi\n\n"
            f"👷 Topilgan ustalar soni: {len(masters)}"
        )

        bot.send_message(
            user_id,
            text_result
        )

        user_search_step.pop(user_id, None)

        return

    # ================== BOSH MENYU ==================

    if text == "⬅️ Bosh menyu":

        user_mode[user_id] = None

        hammom_bot.user_step.pop(user_id, None)
        isitish_bot.user_step.pop(user_id, None)

        show_main_menu(user_id)

        return

    # ================== YANGI HISOB ==================

    if text == "🔄 Yangi hisob":

        mode = user_mode.get(user_id)

        if mode == "hammom":
            hammom_bot.start(user_id, bot)

        elif mode == "isitish":
            isitish_bot.start(user_id, bot)

        else:
            show_main_menu(user_id)

        return

    # ================== MODUL TANLASH ==================

    if text == "🚿 Hammom hisoblash":

        user_mode[user_id] = "hammom"

        isitish_bot.user_step.pop(user_id, None)

        hammom_bot.start(user_id, bot)

        return

    if text == "🔥 Isitish tizimi":

        user_mode[user_id] = "isitish"

        hammom_bot.user_step.pop(user_id, None)

        isitish_bot.start(user_id, bot)

        return

    # ================== MODE TANLANMAGAN ==================

    if user_mode[user_id] is None:

        show_main_menu(user_id)

        return

    # ================== MODULE ROUTING ==================

    if user_mode[user_id] == "hammom":

        result = hammom_bot.handle(message, bot)

        if isinstance(result, dict):

            materials = result["materials"]
            equipment = result["equipment"]

            cursor.execute("""
                SELECT lat, lon
                FROM users
                WHERE user_id=?
            """, (user_id,))

            row = cursor.fetchone()

            if row:

                lat, lon = row

                shops = find_nearby_shops(
                    cursor,
                    lat,
                    lon,
                    radius=10
                )

                all_items = {}

                all_items.update(materials)
                all_items.update(equipment)

                material_sum, usta_sum, jami_sum = calculate_estimate(all_items)

                client_name = client_names.get(
                    user_id,
                    "Noma'lum"
                )

                clean_materials = {
                    k: v
                    for k, v in materials.items()
                    if isinstance(v, (int, float)) and v > 0
                }

                text_send = (
                    "📦 YANGI SMETA\n\n"
                    f"👤 Mijoz: {client_name}\n"
                    f"👷 Usta: {message.from_user.first_name}\n\n"
                    + format_result(clean_materials, equipment)
                )

                text_send += "\n━━━━━━━━━━━━━━━\n"
                text_send += f"💰 TAXMINIY MATERIAL: {material_sum:,} so'm\n"

                markup = types.InlineKeyboardMarkup()

                markup.add(
                    types.InlineKeyboardButton(
                        "💰 Taklif yuborish",
                        callback_data=f"estimate_offer_{user_id}"
                    )
                )

                for shop in shops:

                    try:

                        bot.send_message(
                            shop["user_id"],
                            text_send,
                            reply_markup=markup
                        )

                    except Exception as e:
                        print(
                            f"SHOP SEND ERROR: {shop['user_id']} -> {e}"
                        )

        return

    if user_mode[user_id] == "isitish":

        result = isitish_bot.handle(message, bot)

        if isinstance(result, dict):

            materials = result["materials"]
            equipment = result["equipment"]

            cursor.execute("""
                SELECT lat, lon
                FROM users
                WHERE user_id=?
            """, (user_id,))

            row = cursor.fetchone()

            if row:

                lat, lon = row

                shops = find_nearby_shops(
                    cursor,
                    lat,
                    lon,
                    radius=10
                )

                for shop in shops:

                    try:

                        client_name = client_names.get(
                            user_id,
                            "Noma'lum"
                        )

                        all_items = {}

                        all_items.update(materials)
                        all_items.update(equipment)

                        material_sum, usta_sum, jami_sum = calculate_estimate(all_items)

                        estimate_text = format_result(
                            materials,
                            equipment
                        )

                        text_send = (
                            "📦 YANGI SMETA\n\n"
                            f"👤 Mijoz: {client_name}\n"
                            f"👷 Usta: {message.from_user.first_name}\n\n"
                            f"{estimate_text}\n"
                            "━━━━━━━━━━━━━━━\n"
                            f"💰 TAXMINIY MATERIAL: {material_sum:,} so'm\n"
                        )

                        markup = types.InlineKeyboardMarkup()

                        markup.add(
                            types.InlineKeyboardButton(
                                "💰 Taklif yuborish",
                                callback_data=f"estimate_offer_{user_id}"
                            )
                        )

                        bot.send_message(
                            shop["user_id"],
                            text_send,
                            reply_markup=markup
                        )

                    except Exception as e:
                        print("ISITISH SHOP ERROR:", e)

            return


@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_request(call):

    master_id = call.message.chat.id
    client_id = int(call.data.split("_")[1])

    # 🔥 AGAR OLINGAN BO‘LSA
    if client_id in accepted_requests:
        bot.answer_callback_query(
            call.id,
            "❌ Bu zakaz allaqachon olingan"
        )
        return

    # 👷 USTA INFO
    cursor.execute("""
        SELECT
            name,
            phone,
            rating,
            completed_jobs,
            lat,
            lon
        FROM users
        WHERE user_id=?
    """, (master_id,))
    master = cursor.fetchone()

    # 👤 MIJOZ INFO
    cursor.execute("""
        SELECT
            name,
            phone,
            lat,
            lon
        FROM users
        WHERE user_id=?
    """, (client_id,))
    client = cursor.fetchone()

    if not master or not client:
        bot.answer_callback_query(
            call.id,
            "❌ Foydalanuvchi topilmadi"
        )
        return

    master_name, master_phone, master_rating, completed_jobs, master_lat, master_lon = master
    client_name, client_phone, client_lat, client_lon = client

    distance = calculate_distance(
        client_lat,
        client_lon,
        master_lat,
        master_lon
    )

    # 🔥 ACTIVE ORDER
    accepted_requests.add(client_id)
    active_orders[client_id] = master_id

    # 🔥 BOSHQA USTALARDAN O‘CHIRISH
    for uid, mid in request_messages.get(client_id, []):

        if uid != master_id:
            try:
                bot.delete_message(uid, mid)
            except:
                pass

    # 👤 MIJOZGA
    msg1 = bot.send_message(
        client_id,
        f"✅ Usta topildi\n\n"
        f"👷 {master_name}\n"
        f"⭐ {master_rating:.1f}\n"
        f"🛠 {completed_jobs} ta ish bajarilgan\n"
        f"📍 {distance:.1f} km uzoqda\n"
        f"📞 {master_phone}\n\n"
        f"✅ Ish tugagach ustani baholang:"
    )

    threading.Timer(
        300,
        auto_delete,
        args=(client_id, msg1.message_id)
    ).start()

    # 👷 USTAGA
    msg2 = bot.send_message(
        master_id,
        f"📞 Mijoz kontakti\n\n"
        f"👤 {client_name}\n"
        f"📞 {client_phone}"
    )

    try:
        bot.delete_message(master_id, call.message.message_id)
    except:
        pass

    if client_lat and client_lon:
        bot.send_location(
            master_id,
            client_lat,
            client_lon
        )

    threading.Timer(
        300,
        auto_delete,
        args=(master_id, msg2.message_id)
    ).start()

    bot.answer_callback_query(
        call.id,
        "Zakaz qabul qilindi"
    )
#______ha______

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("cancel_order_yes_")
)
def cancel_order_yes(call):

    client_id = int(call.data.split("_")[3])

    accepted_requests.discard(client_id)
    active_orders.pop(client_id, None)

    user_search_step[client_id] = "waiting_problem"

    bot.edit_message_text(
        "✅ Eski buyurtma bekor qilindi.\n\n"
        "🛠 Muammoni yozing:",
        call.message.chat.id,
        call.message.message_id
    )

    bot.answer_callback_query(
        call.id,
        "Buyurtma bekor qilindi"
    )
#_______yo'q______

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("cancel_order_no_")
)
def cancel_order_no(call):

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

    bot.answer_callback_query(
        call.id,
        "Bekor qilindi"
    )

# ================== RATING ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("rate_"))
def rate_master(call):

    data = call.data.split("_")

    master_id = int(data[1])
    rating = int(data[2])

    # 🔥 ESKI RATING
    cursor.execute("""
        SELECT rating, rating_count
        FROM users
        WHERE user_id=?
    """, (master_id,))

    row = cursor.fetchone()

    if not row:
        return

    old_rating, count = row

    # 🔥 YANGI RATING
    new_count = count + 1

    new_rating = (
        (old_rating * count) + rating
    ) / new_count

    # 🔥 SAVE
    cursor.execute("""
        UPDATE users
        SET rating=?,
            rating_count=?,
            completed_jobs = completed_jobs + 1
        WHERE user_id=?
    """, (
        new_rating,
        new_count,
        master_id
    ))

    conn.commit()

    bot.answer_callback_query(
        call.id,
        "⭐ Baho uchun rahmat"
    )

    bot.send_message(
        call.message.chat.id,
        "✅ Usta baholandi"
    )

    # 🔥 ORDER CLEAN
    for client_id, mid in list(active_orders.items()):

        if mid == master_id:

            active_orders.pop(client_id, None)

            if client_id in accepted_requests:
                accepted_requests.remove(client_id)
    # 🔥 REYTING XABARINI O'CHIRISH

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

# ================== SHOP OFFER ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("offer_"))
def shop_offer(call):

    shop_id = call.message.chat.id

    client_id = int(call.data.split("_")[1])

    shop_offer_step[shop_id] = "waiting_offer"
    shop_offer_client[shop_id] = client_id

    bot.send_message(
        shop_id,
        "💰 Taklif narxini yuboring:"
    )

    bot.answer_callback_query(
        call.id,
        "Taklif yuborish boshlandi"
    )

# ================== ESTIMATE OFFER ==================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("estimate_offer_")
)
def estimate_offer(call):

    shop_id = call.message.chat.id

    client_id = int(
        call.data.replace(
            "estimate_offer_",
            ""
        )
    )

    estimate_offer_step[shop_id] = "waiting_offer"

    estimate_offer_client[shop_id] = client_id

    bot.send_message(
        shop_id,
        "💰 Smeta uchun taklif narxini yuboring:"
    )

    bot.answer_callback_query(
        call.id,
        "Smeta taklifi boshlandi"
    )

    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
    except:
        pass

# ================== SHOP HAVE PRODUCT ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_have_"))
def shop_have_product(call):

    shop_id = call.from_user.id

    client_id = int(call.data.split("_")[2])

    shop_offer_client[shop_id] = client_id

    shop_offer_step[shop_id] = "waiting_offer"

    bot.send_message(
        shop_id,
        "💰 Mahsulot narxini yozing"
    )

    bot.answer_callback_query(
        call.id,
        "✅ Narxni yuboring"
    )

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("delivery_")
        and not call.data.startswith("delivery_yes_")
        and not call.data.startswith("delivery_no_")
)
def delivery_request(call):

    master_id = call.from_user.id
    parts = call.data.split("_")

    if len(parts) != 3:
        bot.answer_callback_query(call.id, "Xatolik")
        return

    requester_id = int(parts[1])   # usta
    shop_id = int(parts[2])        # do‘kon

    # 🔥 DO'KONLARDAGI REQUESTLARNI O'CHIRISH
    for uid, mid in product_request_messages.get(requester_id, []):
        try:
            bot.delete_message(uid, mid)
        except:
            pass

    product_request_messages.pop(requester_id, None)

    delivery_step[master_id] = {
        "requester_id": requester_id,
        "shop_id": shop_id
    }

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    markup.add(
        types.KeyboardButton(
            "📍 Lokatsiya yuborish",
            request_location=True
        )
    )

    bot.send_message(
        master_id,
        "📍 Yetkazib berish uchun lokatsiyangizni yuboring:",
        reply_markup=markup
    )

    bot.answer_callback_query(
        call.id,
        "Lokatsiya yuboring"
    )

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

# ================== ACCEPT ESTIMATE ==================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("estimate_accept_")
)
def accept_estimate(call):

    parts = call.data.split("_")

    if len(parts) != 4:
        bot.answer_callback_query(call.id, "Xatolik")
        return

    master_id = int(parts[2])   # usta
    shop_id = int(parts[3])     # do'kon

    cursor.execute("""
        SELECT name, phone
        FROM users
        WHERE user_id=?
    """, (master_id,))
    master = cursor.fetchone()

    cursor.execute("""
        SELECT name, phone, lat, lon
        FROM users
        WHERE user_id=?
    """, (shop_id,))
    shop = cursor.fetchone()

    if not master or not shop:
        bot.answer_callback_query(
            call.id,
            "Ma'lumot topilmadi"
        )
        return

    master_name, master_phone = master

    shop_name, shop_phone, shop_lat, shop_lon = shop

    # ================== USTAGA ==================

    bot.send_message(
        master_id,
        f"✅ Taklif qabul qilindi\n\n"
        f"🏪 Do'kon: {shop_name}\n"
        f"📞 {shop_phone}"
    )

    if shop_lat and shop_lon:

        bot.send_location(
            master_id,
            shop_lat,
            shop_lon
        )

    # ================== DO'KONGA ==================

    bot.send_message(
        shop_id,
        f"✅ Usta taklifingizni qabul qildi\n\n"
        f"👷 Usta: {master_name}\n"
        f"📞 {master_phone}"
    )

    # 🔥 SAVDO TEKSHIRISH UCHUN SAQLASH

    estimate_sales_check[shop_id] = {
        "master_id": master_id
    }

    # 🔥 1 SOATDAN KEYIN TEKSHIRISH

    def ask_estimate_sale():

        if shop_id not in estimate_sales_check:
            return

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "✅ Ha",
                callback_data=f"estimate_sold_yes_{shop_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Yo'q",
                callback_data=f"estimate_sold_no_{shop_id}"
            )
        )

        bot.send_message(
            shop_id,
            "📦 Ushbu smeta sotildimi?",
            reply_markup=markup
        )

    threading.Timer(
        3600,
        ask_estimate_sale
    ).start()

    bot.answer_callback_query(
        call.id,
        "Kontaktlar almashildi"
    )

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

# ================== PRODUCT SENT ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("sent_"))
def sent_product(call):

    parts = call.data.split("_")

    requester_id = int(parts[1])
    shop_id = int(parts[2])

    markup = types.InlineKeyboardMarkup()

    for minute in [10, 20, 30, 40, 50, 60]:

        markup.add(
            types.InlineKeyboardButton(
                f"{minute} daqiqa",
                callback_data=f"time_{requester_id}_{shop_id}_{minute}"
            )
        )

    bot.send_message(
        shop_id,
        "⏱ Taxminiy yetib borish vaqtini tanlang:",
        reply_markup=markup
    )

    bot.answer_callback_query(
        call.id,
        "Vaqtni tanlang"
    )

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

# ================== DELIVERY TIME ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def delivery_time(call):

    parts = call.data.split("_")

    requester_id = int(parts[1])
    shop_id = int(parts[2])
    minute = int(parts[3])

    # 🔥 SHOP SALES +1
    cursor.execute("""
        UPDATE users
        SET shop_sales = shop_sales + 1
        WHERE user_id=?
    """, (shop_id,))
    conn.commit()

    bot.send_message(
        requester_id,
        f"📦 Mahsulot yuborildi\n\n"
        f"⏱ Taxminiy yetib borish vaqti: {minute} daqiqa"
    )

    bot.send_message(
        shop_id,
        "✅ Yetkazib berish vaqti yuborildi"
    )

    def ask_delivery_confirm():
        start = time.time()

        time.sleep(minute * 60)

        finish = time.time()

        markup = types.InlineKeyboardMarkup()

        markup.row(
            types.InlineKeyboardButton(
                "✅ Ha",
                callback_data=f"delivery_yes_{requester_id}_{shop_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Yo'q",
                callback_data=f"delivery_no_{requester_id}_{shop_id}"
            )
        )

        send_replace(
            bot,
            requester_id,
            "📦 Mahsulot yetib keldimi?",
            reply_markup=markup
        )

    threading.Thread(target=ask_delivery_confirm, daemon=False).start()

    bot.answer_callback_query(
        call.id,
        "Vaqt yuborildi"
    )

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

# ================== DELIVERY YES ==================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("delivery_yes_")
)
def delivery_yes(call):

    parts = call.data.split("_")

    requester_id = int(parts[2])
    shop_id = int(parts[3])

    markup = types.InlineKeyboardMarkup()

    for i in range(1, 6):
        markup.add(
            types.InlineKeyboardButton(
                f"⭐ {i}",
                callback_data=f"shoprate_{shop_id}_{i}"
            )
        )

    bot.send_message(
        requester_id,
        "⭐ Do‘kon xizmatini baholang:",
        reply_markup=markup
    )

    bot.answer_callback_query(
        call.id,
        "Rahmat"
    )

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

# ================== DELIVERY NO ==================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("delivery_no_")
)
def delivery_no(call):

    parts = call.data.split("_")

    requester_id = int(parts[2])
    shop_id = int(parts[3])

    bot.send_message(
        requester_id,
        "❌ Mahsulot hali yetib kelmadi deb belgilandi."
    )

    bot.send_message(
        shop_id,
        "⚠️ Usta mahsulot hali yetib kelmaganini bildirdi.\n\n"
        "Iltimos, usta bilan bog'laning."
    )

    try:
        bot.edit_message_text(
            "❌ Mahsulot yetib kelmadi",
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

    bot.answer_callback_query(
        call.id,
        "Xabar yuborildi"
    )

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

# ================== SHOP RATING ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("shoprate_"))
def shop_rate(call):

    parts = call.data.split("_")

    shop_id = int(parts[1])
    rating = int(parts[2])

    cursor.execute("""
        SELECT shop_rating, shop_rating_count
        FROM users
        WHERE user_id=?
    """, (shop_id,))
    row = cursor.fetchone()

    if not row:
        bot.answer_callback_query(call.id, "Do‘kon topilmadi")
        return

    old_rating, count = row

    new_count = count + 1
    new_rating = ((old_rating * count) + rating) / new_count

    cursor.execute("""
        UPDATE users
        SET shop_rating=?,
            shop_rating_count=?
        WHERE user_id=?
    """, (
        new_rating,
        new_count,
        shop_id
    ))
    conn.commit()

    bot.answer_callback_query(call.id, "⭐ Baholash uchun rahmat")
    bot.send_message(call.message.chat.id, "✅ Do‘kon baholandi")

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

# ================== ESTIMATE SOLD YES ==================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("estimate_sold_yes_")
)
def estimate_sold_yes(call):

    shop_id = int(call.data.split("_")[3])

    data = estimate_sales_check.get(shop_id)

    if not data:
        bot.answer_callback_query(call.id, "Ma'lumot topilmadi")
        return

    master_id = data["master_id"]

    # 🔥 SAVDO +1

    cursor.execute("""
        UPDATE users
        SET shop_sales = shop_sales + 1
        WHERE user_id=?
    """, (shop_id,))
    conn.commit()

    # 🔥 REYTING

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "⭐ 1",
            callback_data=f"shoprate_{shop_id}_1"
        ),
        types.InlineKeyboardButton(
            "⭐ 2",
            callback_data=f"shoprate_{shop_id}_2"
        ),
        types.InlineKeyboardButton(
            "⭐ 3",
            callback_data=f"shoprate_{shop_id}_3"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            "⭐ 4",
            callback_data=f"shoprate_{shop_id}_4"
        ),
        types.InlineKeyboardButton(
            "⭐ 5",
            callback_data=f"shoprate_{shop_id}_5"
        )
    )

    bot.send_message(
        master_id,
        "⭐ Do'konni baholang:",
        reply_markup=markup
    )

    estimate_sales_check.pop(shop_id, None)

    bot.edit_message_text(
        "✅ Savdo tasdiqlandi",
        call.message.chat.id,
        call.message.message_id
    )

    bot.answer_callback_query(
        call.id,
        "Savdo hisoblandi"
    )

# ================== ESTIMATE SOLD NO ==================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("estimate_sold_no_")
)
def estimate_sold_no(call):

    shop_id = int(call.data.split("_")[3])

    estimate_sales_check.pop(shop_id, None)

    bot.edit_message_text(
        "❌ Savdo amalga oshmadi",
        call.message.chat.id,
        call.message.message_id
    )

    bot.answer_callback_query(
        call.id,
        "Bekor qilindi"
    )

# ================== RUN ==================

print("Bot ishga tushdi...")

bot.infinity_polling(
    timeout=20,
    long_polling_timeout=60
)
