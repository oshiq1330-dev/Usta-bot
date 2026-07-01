def format_result(result, products):

    trubalar = ""
    fitinglar_list = []
    jihozlar = ""
    aksessuar = ""
    isitish = ""
    boshqa = ""

    # 🔥 IGNORE
    IGNORE = {
        "uzunlik",
        "kenglik",
        "pol maydon",
        "kirmashina",
        "maydon",
        "kontur",
        "dush"
    }

    # 🔥 ENG MUHIM — NATIJANI BIRLASHTIRISH
    all_items = result.copy()

    EXCLUDE_PRODUCTS = {
        "panel",
        "section"
    }

    for k, v in products.items():

        if k in EXCLUDE_PRODUCTS:
            continue

        if k not in all_items:
            all_items[k] = v

    # 🔥 ASOSIY LOOP (FAqat Bitta!)
    for name, qty in all_items.items():

    # ❗ ENG MUHIM FIX
        if not isinstance(qty, (int, float)):
            continue

        name_lower = name.lower()
        name_clean = name_lower.replace(" ", "")
        qty = round(qty)

        # Radiator o'lchamlarini o'tkazib yuborish
        if "×" in name and not name_lower.startswith("trap"):
            continue

        if name_lower in ["35 sm", "55 sm"]:
            continue

        if name_lower == "radiator":
            continue

    # ❌ IGNORE
        if name_lower in IGNORE:
            continue

        # 📏 TRUBA
        if "truba" in name_lower and "folgasiz" not in name_lower:
            trubalar += f"• {name} — {qty} metr\n"

        # 🔧 FITTING
        elif any(x in name_clean for x in [
            "atvot",
            "mufta",
            "troynik",
            "ushastik",
            "klipsa",
            "kran",
            "mo'stik",
            "nakidnoy",
            "perexod",
            "amerikanka",
            "adapter"
        ]):
            fitinglar_list.append(f"• {name} — {qty} ta")

        # 🔥 NASOS (maxsus ajratish)
        elif "nasos" in name_lower and "25." in name_lower:
            isitish += f"• {name} — {qty} dona\n"

        elif "bosim" in name_lower:
            aksessuar += f"• {name} — {qty} ta\n"

        # 🔥 TOPLI POL
        elif any(x in name_lower for x in [
            "penaplast", "folga", "gidropara",
            "skoba", "kontur", "kollektor",
            "folgasiz", "datchik", "kabeli",
            "fiksator", "termostat", "kran"
        ]):
            if any(x in name_lower for x in ["truba", "gidropara", "kabel"]):
                unit = "metr"
            else:
                unit = "dona"

            isitish += f"• {name} — {qty} {unit}\n"

        # 🚿 ASOSIY JIHOZ
        elif any(x in name_lower for x in [
            "vanna", "rakvina", "unitaz",
            "dush", "chashagen",
            "yomkist", "boiler", "sushilka",
            "mustahab", "taxorat", "katyol",
            "bak", "radiator", "kollektor (radiator)"
        ]) and not any(x in name_lower for x in [
            "sifon", "smesitel", "kriplena",
            "shlank", "duga", "parda",
            "paplavoy", "filtr", "nasos",
            "xavfsizlik", "trap"
        ]):

            # 🔥 MAXSUS UNIT
            if "katyol" in name_lower:
                unit = "kW"
                name = "Katyol"
            elif "bak" in name_lower:
                unit = "litr"
                name = "Rasshiritel bak"
            else:
                unit = "ta"

            jihozlar += f"• {name} — {qty} {unit}\n"

        # 🧩 AKSESSUAR
        elif any(x in name_lower for x in [
            "sifon", "smesitel", "kriplena",
            "shlank", "duga", "parda",
            "paplavoy", "filtr", "nasos",
            "xavfsizlik", "trap"
        ]):

            aksessuar += f"• {name} — {qty} ta\n"

        # 📦 BOSHQA
        else:
            # 🔥 IZOLYATSIYA UCHUN MAXSUS
            if "izolyatsiya" in name_lower:
                boshqa += f"• {name} — {qty} metr\n"
            else:
                boshqa += f"• {name} — {qty} ta\n"

    text = "📦 MATERIALLAR:\n━━━━━━━━━━━━━━━\n\n"

    if trubalar:
        text += "📏 TRUBALAR:\n" + trubalar + "\n"

    if fitinglar_list:
        fitinglar_list.sort(key=lambda x: x.lower())  # 🔥 ALFAVIT
        text += "🔧 FITTINGLAR:\n" + "\n".join(fitinglar_list) + "\n\n"

    if isitish:
        text += "🔥 TOPLI POL:\n" + isitish + "\n"

    if jihozlar:
        text += "🚿 JIHOZLAR:\n" + jihozlar + "\n"

    # 🔥 PANEL RADIATORLAR (LOOPDAN TASHQARI!)
    panel = products.get("panel", {})
    if panel:
        text += "📦 PANEL RADIATORLAR:\n"
        for size, count in panel.items():
            text += f"• {size} — {count} ta\n"
        text += "\n"

    # 📦 SEKSIONAL RADIATORLAR
    sections = products.get("section", [])

    if sections:
        text += "📦 SEKSIONAL RADIATORLAR:\n"
        for item in sections:
            size = item.get("size", "")
            section = item.get("section", 0)

            text += f"• {size} sm — {section} seksiya\n"
        text += "\n"

    if aksessuar:
        text += "🧩 AKSESSUARLAR:\n" + aksessuar + "\n"

    if boshqa:
        text += "📦 BOSHQA:\n" + boshqa + "\n"

    return text
