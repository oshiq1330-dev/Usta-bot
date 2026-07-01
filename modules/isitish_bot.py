from telebot import types
from core.engine import process
import math
from core.formatter import format_result
from core.state import client_names

user_step = {}
user_data = {}
products = {}
user_choice = {}
last_messages = {}

# ================= PRODUCT =================
def add_product(user_id, name, qty):
    if user_id not in products:
        products[user_id] = {}

    try:
        qty = float(qty)
    except:
        return  # xato qiymatni tashlab ketamiz

    old = products[user_id].get(name, 0)

    if isinstance(old, dict):
        old = 0

    products[user_id][name] = old + qty

# ================= RADIATOR =================
RADIATOR_SIZES = [
"30×40", "40×40", "50×40", "60×40",
"30×60", "40×60", "50×60", "60×60",
"30×80", "40×80", "50×80", "60×80",
"30×100","40×100","50×100","60×100",
"30×120","40×120","50×120","60×120",
"30×140","40×140","50×140","60×140",
"30×160","40×160","50×160","60×160",
"30×180","40×180","50×180","60×180",
"30×200","40×200","50×200","60×200",
]

def radiator_type_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Panelniy", "Seksiyalik")
    markup.row("✅ Hisoblash")
    return markup


def panel_keyboard(selected_height=None):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # 🔝 DOIMIY BALANDLIKLAR
    markup.row("30", "40", "50", "60")

    # 🔥 AGAR TANLANGAN BO‘LSA → O‘LCHAMLAR
    if selected_height:
        sizes = [s for s in RADIATOR_SIZES if s.startswith(selected_height + "×")]

        for i in range(0, len(sizes), 3):
            markup.row(*sizes[i:i+3])

    # 🔻 DOIMIY PASTKI QISM
    markup.row("💾 Saqlash", "⬅️ Orqaga")

    return markup


# ================= START =================
def start(user_id, bot):

    user_step[user_id] = "client_name"

    products[user_id] = {}
    user_data[user_id] = {}

    bot.send_message(
        user_id,
        "👤 Mijoz ismini kiriting:"
    )

# ================= HANDLE =================
def handle(message, bot):
    user_id = message.chat.id
    text = message.text.strip()
    step = user_step.get(user_id)

    # 🔥 GLOBAL MENU BLOCK
    if text in [
        "🚿 Hammom hisoblash",
        "🔥 Isitish tizimi",
        "⬅️ Bosh menyu",
        "🔄 Yangi hisob"
    ]:
        return

    step = user_step.get(user_id)


    # ---------- START ----------
    if step == "start":
        start(user_id, bot)
        return

    # ---------- CLIENT NAME ----------
    if step == "client_name":

        client_names[user_id] = text

        user_step[user_id] = "uzunlik"

        bot.send_message(
            user_id,
            "📏 Hovli yoki Honadon uzunligini kiriting:"
        )

        return

    # ---------- UZUNLIK ----------
    if step == "uzunlik":
        try:
            products[user_id]["Uzunlik"] = float(text)
        except:
            bot.send_message(user_id, "❌ Iltimos raqam kiriting")
            return

        user_step[user_id] = "kenglik"
        bot.send_message(user_id, "📏 Hovli yoki Honadon kengligini kiriting:")
        return


    # ---------- KENGLIK ----------
    elif step == "kenglik":
        try:
            products[user_id]["Kenglik"] = float(text)
        except:
            bot.send_message(user_id, "❌ Iltimos raqam kiriting")
            return

        user_step[user_id] = "topli_pol"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Ha", "Yo'q")

        bot.send_message(user_id, "♨️ Topli pol bormi?", reply_markup=markup)
        return

    # ---------- TOPLI POL ----------
    elif step == "topli_pol":

        if text == "Ha":
            user_step[user_id] = "pol_maydon"
            bot.send_message(user_id, "📐 Topli pol maydonini (m²) kiriting:")
            return

        elif "Yo'q" in text:
            user_choice[user_id] = "yo'q"

            # 🔥 ENG MUHIM FIX
            products[user_id]["Pol maydon"] = 0

            user_step[user_id] = "radiator_type"

            bot.send_message(
                user_id,
                "🔥 Radiator turini tanlang:",
                reply_markup=radiator_type_keyboard()
            )
            return


    # ---------- POL ----------
    elif step == "pol_maydon":
        try:
            products[user_id]["Pol maydon"] = float(text)
            user_choice[user_id] = "pol"
        except:
            bot.send_message(user_id, "❌ Iltimos raqam kiriting")
            return

        user_step[user_id] = "radiator_type"
        bot.send_message(
            user_id,
            "🔥 Radiator turini tanlang:",
            reply_markup=radiator_type_keyboard()
        )
        return


    # ---------- RADIATOR TYPE ----------
    elif step == "radiator_type":

        if text == "Panelniy":
            user_step[user_id] = "panel_height"
            bot.send_message(user_id, "📏 Radiator balandligini tanlang:", reply_markup=panel_keyboard())
            return

        elif text == "Seksiyalik":
            user_step[user_id] = "section_size"

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("35", "55")
            markup.row("⬅️ Orqaga")

            bot.send_message(user_id, "📏 Radiator o'lchamini tanlang:", reply_markup=markup)
            return

        elif "Hisoblash" in text:
            user_step[user_id] = "system"

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Samatok", "2 Trubalik", "Luchavoy")

            bot.send_message(user_id, "🔧 Isitish tizimini tanlang:", reply_markup=markup)
            return


    # ---------- PANEL ----------
    elif step == "panel_height":

        if text == "⬅️ Orqaga":
            user_step[user_id] = "radiator_type"
            bot.send_message(user_id, "🔙", reply_markup=radiator_type_keyboard())
            return

        if text in ["30", "40", "50", "60"]:
            user_data[user_id]["height"] = text
            user_step[user_id] = "panel_size"

            bot.send_message(
                user_id,
                f"📏 {text} balandlik tanlandi",
                reply_markup=panel_keyboard(text)
            )
            return


    elif step == "panel_size":

        if "panel" not in products[user_id]:
            products[user_id]["panel"] = {}

        if text == "⬅️ Orqaga":
            user_step[user_id] = "radiator_type"
            bot.send_message(user_id, "🔙", reply_markup=radiator_type_keyboard())
            return

        elif text == "💾 Saqlash":

            msg = "🔥 Panel radiator:\n\n"

            for k, v in products[user_id]["panel"].items():
                msg += f"{k} → {v} ta\n"

            bot.send_message(
                user_id,
                msg
            )

            user_step[user_id] = "radiator_type"
            bot.send_message(user_id, "Davom eting:", reply_markup=radiator_type_keyboard())
            return

        # 🔥 BALANDLIK BOSILSA (MUHIM!)
        elif text in ["30", "40", "50", "60"]:
            user_data[user_id]["height"] = text

            bot.send_message(
                user_id,
                f"📏 {text} ga o‘tdingiz",
                reply_markup=panel_keyboard(text)
            )
            return

        # 🔥 SIZE BOSILSA
        elif "×" in text:

            products[user_id]["panel"][text] = products[user_id]["panel"].get(text, 0) + 1

            qty = products[user_id]["panel"][text]

            bot.send_message(
                user_id,
                f"✅ {text} → {qty} ta",
                reply_markup=panel_keyboard(user_data[user_id].get("height"))
            )
            return


    # ---------- SEKSIONAL ----------
    elif step == "section_size":

        if text == "⬅️ Orqaga":
            user_step[user_id] = "radiator_type"
            bot.send_message(user_id, "🔙", reply_markup=radiator_type_keyboard())
            return

        try:
            user_data[user_id]["section_size"] = int(text)
        except:
            bot.send_message(user_id, "❌ Iltimos raqam tanlang")
            return

        user_step[user_id] = "section_count"

        bot.send_message(user_id, "Nechta tochka? (radiator sonini kiriting)")
        return


    elif step == "section_count":

        try:
            user_data[user_id]["count"] = int(text)
        except:
            bot.send_message(user_id, "❌ Iltimos raqam kiriting")
            return

        user_step[user_id] = "section_qty"
        bot.send_message(user_id, "Nechta seksiya? (seksiya sonini kiriting)")
        return


    elif step == "section_qty":

        try:
            qty = int(text)
        except:
            bot.send_message(user_id, "❌ Iltimos raqam kiriting")
            return

        if "section" not in products[user_id]:
            products[user_id]["section"] = []

        products[user_id]["section"].append({
            "size": user_data[user_id]["section_size"],
            "count": user_data[user_id]["count"],
            "section": qty
        })


        bot.send_message(user_id, "✅ Qo‘shildi")

        user_step[user_id] = "radiator_type"
        bot.send_message(user_id, "Davom eting:", reply_markup=radiator_type_keyboard())
        return


    # ---------- SYSTEM ----------
    elif step == "system":

        if text not in ["Samatok", "2 Trubalik", "Luchavoy"]:
            bot.send_message(user_id, "❌ Iltimos tugma tanlang")
            return

        # 🔥 UZUNLIK / KENGLIK
        uzunlik = float(products[user_id].get("Uzunlik", 0) or 0)
        kenglik = float(products[user_id].get("Kenglik", 0) or 0)

        maydon = uzunlik * kenglik
        pol_maydon = float(products[user_id].get("Pol maydon", 0) or 0)

        # 🔥 KATYOL (UMUMIY MAYDON)
        total_maydon = maydon + pol_maydon
        katyol = round(total_maydon / 10)
        add_product(user_id, "Katyol (kW)", katyol)

        # 🔥 FILTR
        add_product(user_id, "Filtr", 1)

        termostat = 1

        # 🔥 TRUBA / KATYOL BLOK
        add_product(user_id, "Truba 25 (issiq)", 4)
        add_product(user_id, "Adapter 40 tashqi", 2)
        add_product(user_id, "Xavfsizlik guruhi", 1)

        bak = 20 if katyol <= 15 else 30
        add_product(user_id, "Rasshiritel bak", bak)

        add_product(user_id, "Adapter 25x1/2 ichki", 2)
        add_product(user_id, "Amerikanka 25 ichki", 2)
        add_product(user_id, "FUM lenta", 1)
        add_product(user_id, "Jidkiy FUM", 1)
        add_product(user_id, "Kran 25", 2)
        add_product(user_id, "Atvot 90° 25", 8)
        add_product(user_id, "Termo datchik", 1)
        add_product(user_id, "Atvot 45° 25", 4)
        add_product(user_id, "Mufta 25", 2)

        # 🔥 RADIATOR HISOB
        radiator = 0

        for v in products[user_id].get("panel", {}).values():
            if isinstance(v, (int, float)):
                radiator += v

        for item in products[user_id].get("section", []):
            count = item.get("count", 0)
            if isinstance(count, (int, float)):
                radiator += count

        products[user_id]["Radiator"] = radiator

        # Panel radiatorlarni materiallarga qo'shish
        for model, qty in products[user_id].get("panel", {}).items():
            add_product(user_id, model, qty)

        # Seksiyalik radiatorlarni materiallarga qo'shish
        for item in products[user_id].get("section", []):

            size = item.get("size")
            section_qty = item.get("section", 0)

            if size == 35:
                add_product(user_id, "35 sm", section_qty)

            elif size == 55:
                add_product(user_id, "55 sm", section_qty)

        # 🔥 NASOS (faqat radiator uchun)
        if radiator > 0:
            if radiator <= 6:
                add_product(user_id, "Nasos 32.4.180", 1)
            elif radiator <= 12:
                add_product(user_id, "Nasos 32.6.180", 1)
            else:
                add_product(user_id, "Nasos 32.8.180", 1)

        # ================= TOPLI POL =================
        kollektorlar = []
        kollektor_soni = 0
        kontur = 0

        # 🔥 FAQAT USER KIRITGAN MAYDON
        if pol_maydon > 0:

            penaplast = round(pol_maydon / 0.7 + 2)
            add_product(user_id, "Penaplast", penaplast)

            folga = round(pol_maydon * 1.05)
            add_product(user_id, "Gidropara (folga)", folga)

            truba16 = round(pol_maydon * 7)


            add_product(user_id, "Truba 16 (folgasiz)", truba16)

            skoba = truba16 * 3
            add_product(user_id, "Skoba", skoba)

            kontur = truba16 // 66
            if truba16 % 66 > 33:
                kontur += 1

            add_product(user_id, "Kontur", kontur)

            if kontur > 0:
                kollektor_soni = math.ceil(kontur / 11)

                base = kontur // kollektor_soni
                qoldiq = kontur % kollektor_soni

                for i in range(kollektor_soni):
                    kollektorlar.append(base + 1 if i < qoldiq else base)

                for k in kollektorlar:
                    add_product(user_id, f"Kollektor {k} kontur", 1)

            if kollektor_soni > 0:
                add_product(user_id, "Troynik 32×1/2", kollektor_soni)
                add_product(user_id, "Nasos 25.6.130", kollektor_soni)
                add_product(user_id, "Kollektor smesitel", kollektor_soni)
                add_product(user_id, "Kollektor kran", kollektor_soni * 2)
                add_product(user_id, "Nakidnoy 32/25", kollektor_soni * 2)
                add_product(user_id, "Kollektor robakal", kollektor_soni * 2)
                add_product(user_id, "Amerikanka 32 tashqi", kollektor_soni * 2)
                add_product(user_id, "Truba 32 (issiq)", kollektor_soni * 6)
                add_product(user_id, "Adapter 25×1/2 ichki", kollektor_soni)

            if kontur > 0:
                add_product(user_id, "Kollektor ftulka", kontur * 2)
                add_product(user_id, "Fiksator", kontur * 2)
                add_product(user_id, "Izolyatsiya 16", kontur)

            # 🔥 TERMOSTAT
            termostat_final = 1 + kollektor_soni
            add_product(user_id, "Termostat", termostat_final)

        # ================= SAMATOK =================
        if text == "Samatok":

            magistral = (uzunlik + kenglik) * 2

            if magistral < 20:
                add_product(user_id, "Truba 32 (issiq)", magistral)
            elif magistral <= 40:
                add_product(user_id, "Truba 32 (issiq)", magistral / 2)
                add_product(user_id, "Truba 40 (issiq)", magistral / 2)
            else:
                add_product(user_id, "Truba 32 (issiq)", magistral / 3)
                add_product(user_id, "Truba 40 (issiq)", magistral / 3)
                add_product(user_id, "Truba 50 (issiq)", magistral / 3)

            # 🔥 RADIATOR TRUBA
            if radiator > 0:
                add_product(user_id, "Truba 25 (issiq)", radiator * 5)

            truba = {
                25: float(products[user_id].get("Truba 25 (issiq)", 0) or 0),
                32: float(products[user_id].get("Truba 32 (issiq)", 0) or 0),
                40: float(products[user_id].get("Truba 40 (issiq)", 0) or 0),
                50: float(products[user_id].get("Truba 50 (issiq)", 0) or 0),
            }

            # 🔥 MAGISTRAL ATVOT (UZUNLIKKA QARAB)
            max_d = 0

            for d in [32, 40, 50]:
                if truba[d] > 0:
                    qty = math.ceil(truba[d] / 10) * 4
                    add_product(user_id, f"Atvot 90° {d}", qty)

                    # 🔥 ENG KATTASINI TOPISH
                    max_d = max(max_d, d)


            # 🔥 KATYOL UCHUN QO‘SHIMCHA ATVOT
            if max_d > 0:
                add_product(user_id, f"Atvot 90° {max_d}", 4)

            # 🔥 RADIATOR ATVOT
            if radiator > 0:
                add_product(user_id, "Atvot 90° 25", radiator * 4)
                add_product(user_id, "Atvot 90° 32", radiator)
                add_product(user_id, "Kran 25×1/2 (radiator)", radiator * 2)

            # 🔥 TROY NIKLAR (magistralga qarab — faqat bitta yo‘l)

            if truba[50] > 0:
                add_product(user_id, "Troynik 50×50", 2)
                add_product(user_id, "Troynik 50×40", 2)
                add_product(user_id, "Troynik 50×32", 2)

            if truba[40] > 0:
                add_product(user_id, "Troynik 40×40", 2)
                add_product(user_id, "Troynik 40×32", 2)

            if truba[32] > 0:
                add_product(user_id, "Troynik 32×32", 2)

            if truba[25] > 0:
                add_product(user_id, "Troynik 25×25", 2)


            # 🔥 RADIATOR TROYNIK (TAQSIMLAB BERAMIZ)

            if radiator > 0:

                total = radiator * 2

                sizes = []

                if truba[50] > 0:
                    sizes.append(50)
                if truba[40] > 0:
                    sizes.append(40)
                if truba[32] > 0:
                    sizes.append(32)

                if sizes:
                    parts = len(sizes)
                    base = total // parts
                    remainder = total % parts

                    sizes.sort(reverse=True)

                    for i, size in enumerate(sizes):
                        qty = base + (1 if i < remainder else 0)
                        add_product(user_id, f"Troynik {size}×25", qty)

            # 🔥 MAGISTRAL ATVOT 45

                if truba[d] > 0:
                    qty = math.ceil(truba[d] / 10) * 2   # 👈 90° dan kamroq
                    add_product(user_id, f"Atvot 45° {d}", qty)

                    max_d = max(max_d, d)

            # 🔥 KATYOL UCHUN 45° (ixtiyoriy)
            if max_d > 0:
                add_product(user_id, f"Atvot 45° {max_d}", 2)


            # 🔥 ATVOT 45° 25 (birlashtirilgan)

            atvot25 = 4  # katyol + bak

            if radiator > 0:
                atvot25 += radiator * 2

            add_product(user_id, "Atvot 45° 25", atvot25)

            # 🔥 TRUBA RAZMERINI TOPISH
            max_size = 0

            for name, qty in products[user_id].items():

                if "truba" in name.lower():

                    # faqat issiq trubalar
                    if "issiq" in name.lower():

                        # raqamni ajratamiz
                        for size in [20, 25, 32, 40, 50]:
                            if str(size) in name:
                                max_size = max(max_size, size)

            # 🔥 AGAR TOPILSA
            if max_size > 0:
                add_product(user_id, f"Amerikanka {max_size} tashqi", 2)

            # 🔥 KATYOL TROY NIK (hammasi chiqishi mumkin — shuning uchun IF)

            if truba[50] > 0:
                add_product(user_id, "Troynik 50×25", 2)

            elif truba[40] > 0:
                add_product(user_id, "Troynik 40×25", 2)

            elif truba[32] > 0:
                add_product(user_id, "Troynik 32×25", 2)

            # 🔥 MUFTA
            for d in [25, 32, 40, 50]:
                if truba[d] > 0:
                    add_product(user_id, f"Mufta {d}", math.ceil(truba[d] / 4))


            # 🔥 PEREXOD (DUPLICATE OLDINI OLAMIZ)

            if truba[50] > 0:
                add_product(user_id, "Perexod 50×40", 4)
                add_product(user_id, "Perexod 50×32", 2)
                add_product(user_id, "Perexod 50×25", 2)

            # 40 → faqat 50 yo‘q bo‘lsa
            if truba[40] > 0 and truba[50] == 0:
                add_product(user_id, "Perexod 40×32", 4)
                add_product(user_id, "Perexod 40×25", 2)

            # 🔥 RADIATOR PEREXOD
            if radiator > 0:
                add_product(user_id, "Perexod 32×25", radiator)

            # 🔥 NASOS UCHUN PEREXOD
            if max_d == 50:
                add_product(user_id, "Perexod 50×40", 2)

            elif max_d == 32:
                add_product(user_id, "Perexod 40×32", 2)


            # 🔥 KLIPSA
            for d in [25, 32, 40, 50]:
                if truba[d] > 0:
                    add_product(user_id, f"Klipsa {d}", truba[d] * 3)


            # 🔥 ANKER
            jami_klipsa = (
                products[user_id].get("Klipsa 25", 0)
                + products[user_id].get("Klipsa 32", 0)
                + products[user_id].get("Klipsa 40", 0)
                + products[user_id].get("Klipsa 50", 0)
            )

            if jami_klipsa > 0:
                add_product(user_id, "Anker dyubel", jami_klipsa)

        # ================= 2 TRUBALIK =================
        elif text == "2 Trubalik":

            perimetr = (uzunlik + kenglik) * 1.5
            truba_length = round(perimetr * 2)

            # 🔥 DIAMETR TANLASH
            if truba_length <= 30:
                diametr = 25
            elif truba_length <= 60:
                diametr = 32
            elif truba_length <= 120:
                diametr = 40
            else:
                diametr = 50

            add_product(user_id, f"Truba {diametr} (issiq)", truba_length)

            # 🔥 RADIATOR
            if radiator > 0:
                add_product(user_id, "Truba 20 (issiq)", radiator * 2)
                add_product(user_id, "Kran 20×1/2 (radiator)", radiator * 2)
                add_product(user_id, "Atvot 90° 20", radiator * 4)

            # 🔥 ATVOT 90° (birlashtirilgan)
            atvot90 = math.ceil(truba_length / 10) * 2 + 4
            add_product(user_id, f"Atvot 90° {diametr}", atvot90)

            # 🔥 TROYNIK
            if radiator > 0:
                add_product(user_id, f"Troynik {diametr}×20", radiator * 2)

            truba_main = truba_length

            # 🔥 MUFTA
            add_product(user_id, f"Mufta {diametr}", math.ceil(truba_main / 4))

            # 🔥 MUFTA 20
            if radiator > 0:
                truba20 = radiator * 1
                add_product(user_id, "Mufta 20", math.ceil(truba20 / 2))

            # 🔥 ATVOT 45°
            atvot45 = math.ceil(truba_main / 10) * 1
            add_product(user_id, f"Atvot 45° {diametr}", atvot45)

            if radiator > 0:
                add_product(user_id, "Atvot 45° 20", radiator * 2)

            # 🔥 KLIPSA
            add_product(user_id, f"Klipsa {diametr}", truba_main * 3)

            if radiator > 0:
                klipsa20 = radiator * 5
                add_product(user_id, "Klipsa 20", klipsa20)
            else:
                klipsa20 = 0

            # 🔥 ANKER
            jami_klipsa = truba_main * 3 + klipsa20
            add_product(user_id, "Anker dyubel", jami_klipsa)

        # ================= LUCHAVOY =================
        elif text == "Luchavoy":

            if radiator > 0:
                perimetr = (uzunlik + kenglik) * 2
                markaz = perimetr / 8
                kontur_truba = (markaz * 2) + 2
                truba16 = round(kontur_truba * radiator)

                add_product(user_id, "Truba 16 (folgalik)", truba16)

            truba_main = round(uzunlik * 2)

            diametr_main = 32 if truba_main <= 20 else 40
            add_product(user_id, f"Truba {diametr_main} (issiq)", truba_main)

            # 🔥 ATVOT (uzunlikka qarab)
            atvot90 = math.ceil(truba_main / 10) * 4 + 4
            atvot45 = math.ceil(truba_main / 10) * 2 + 2

            add_product(user_id, f"Atvot 90° {diametr_main}", atvot90)
            add_product(user_id, f"Atvot 45° {diametr_main}", atvot45)

            # 🔥 MUFTA
            add_product(user_id, f"Mufta {diametr_main}", math.ceil(truba_main / 4))

            # 🔥 PEREXOD
            if diametr_main == 40:
                add_product(user_id, "Perexod 40×32", 2)

            # 🔥 ANKER
            add_product(user_id, "Anker dyubel", truba_main * 2)

            # 🔥 TEMIR LENTA
            lenta = 1 if truba_main <= 100 else 2
            add_product(user_id, "Temir lenta", lenta)

            kontur = radiator

            if kontur > 0:
                add_product(user_id, f"Kollektor (radiator) {kontur} kontur", 1)
                add_product(user_id, "Kollektor robakal", 2)
                add_product(user_id, "Amerikanka 25 ichki", 2)
                add_product(user_id, "Kollektor kran", 2)

            if radiator > 0:
               add_product(user_id, "Sushilka kran", radiator * 2)
               add_product(user_id, "Ushastik topli pol", radiator * 2)
               add_product(user_id, "Udlinitel 10sm", radiator * 2)

        # 🔥 IZOLYATSIYA (RAZMER BO‘YICHA)

        sizes = [16, 20, 25, 32, 40, 50]

        for size in sizes:
            total = 0

            for name, qty in products[user_id].items():

                name_lower = name.lower()

                if "truba" in name_lower:

                    # 🔥 16 faqat folgalik bo‘lsa
                    if size == 16:
                        if "16" in name_lower and "folgalik" in name_lower:
                            if isinstance(qty, (int, float)):
                                total += qty

                    # 🔥 qolgan trubalar
                    else:
                        if f" {size}" in name_lower:
                            if isinstance(qty, (int, float)):
                                total += qty

            if total > 0:
                add_product(user_id, f"Izolyatsiya {size}", total)

        # 🔥 NATIJA
        bot.send_message(user_id, "⏳ Hisoblanmoqda...")

        # ❗ MUHIM: hisoblash funksiyasini ishlat
        result = products[user_id]

        # ❗ ENGINE (hammasini qiladi)
        text = process(user_id, result, products)

        # 🔥 SEND NEW SMETA
        bot.send_message(
            user_id,
            text
        )

        data = {
            "materials": result.copy(),
            "equipment": products[user_id].copy()
        }

        # 🔥 RESET
        products[user_id] = {}

        # 🔥 MENU
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🔄 Yangi hisob")
        markup.row("⬅️ Bosh menyu")

        bot.send_message(user_id, "Tanlang:", reply_markup=markup)

        # 🔥 RESET STEP
        user_step[user_id] = "start"

        return data
