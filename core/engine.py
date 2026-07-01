# core/engine.py

from core.formatter import format_result
from core.estimate import calculate_estimate
from core.shops import find_nearby_shops
from core.db import cursor
from core.db import conn
from core.state import client_names

# 🔹 1. RESULTNI TOZALASH (filter)
def filter_result(result: dict) -> dict:
    return {
        k: v for k, v in result.items()
        if isinstance(v, (int, float)) and v > 0
    }


# 🔹 2. ASOSIY ENGINE
def run_engine(user_id, result, products):

    clean = filter_result(result)

    if not clean:
        return "❌ Hisoblash uchun ma'lumot yetarli emas."

    # ================== CLIENT INFO ==================

    cursor.execute("""
        SELECT name
        FROM users
        WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    # 🔥 MUHIM O'ZGARISH
    client_name = client_names.get(
        user_id,
        "Noma'lum"
    )

    text = (
        f"👤 Mijoz: {client_name}\n\n"
        + format_result(clean, products[user_id])
    )

    all_items = {}

    all_items.update(clean)
    all_items.update(products[user_id])

    material, usta, jami = calculate_estimate(all_items)

    text += "\n━━━━━━━━━━━━━━━\n"
    text += f"💰 TAXMINIY MATERIAL: {material:,} so'm\n"
    text += f"👷 Usta xizmati: {usta:,} so'm\n"
    text += f"💵 TAXMINIY JAMI: {jami:,} so'm\n"

    # ================== USER LOCATION ==================

    cursor.execute("""
        SELECT lat, lon
        FROM users
        WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if row:

        lat, lon = row

        if lat and lon:

            shops = find_nearby_shops(
                cursor,
                lat,
                lon,
                radius=10
            )

            if shops:

                text += "\n━━━━━━━━━━━━━━━\n"
                text += "🏪 YAQIN DO‘KONLAR:\n\n"

                for shop in shops[:5]:

                    text += (
                        f"• {shop['name']}\n"
                        f"📞 {shop['phone']}\n"
                        f"📍 {shop['distance']} km\n\n"
                    )

    text += "\n⚠️ Narxlar taxminiy, bozordagi o‘zgarishga qarab farq qilishi mumkin."
    text += "\n⬆️ Jami summi ichida KATYOL narxi mavjud emas."

    return text


process = run_engine
