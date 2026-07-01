from core.prices import get_price

# 🔥 USTA NARXLAR
USTA_PRICES = {
    "unitaz": 300_000,
    "rakvina": 350_000,
    "vanna": 200_000,
    "dush stayak": 300_000,
    "chashagen": 400_000,

    "mustahab smesitel": 300_000,
    "taxorat smesitel": 300_000,

    "boiler 100l": 300_000,
    "boiler 80l": 300_000,
    "boiler 50l": 300_000,
    "boiler 30l": 300_000,

    "yomkist 1000l": 300_000,
    "yomkist 750l": 300_000,
    "yomkist 650l": 300_000,
    "yomkist 500l": 300_000,
    "yomkist 350l": 300_000,

    "sushilka": 500_000,
    "kirmashina": 200_000,

    "suv filtr": 100_000,
    "bosim uchun nasos 3/4": 100_000,
}


def calculate_estimate(result, system_type=None):

    # =========================
    # 🔥 MATERIAL HISOB
    # =========================

    total = 0

    for name, qty in result.items():

        if not isinstance(qty, (int, float)) or qty <= 0:
            continue

        price = get_price(name)
        total += price * qty

    # =========================
    # 🔥 USTA HISOB
    # =========================

    usta = 0

    for name, qty in result.items():

        if not isinstance(qty, (int, float)) or qty <= 0:
            continue

        name_lower = name.lower()

        for key, price in USTA_PRICES.items():

            if name_lower == key:
                usta += price * qty
                break

    # =========================
    # 🔥 RADIATORLAR
    # =========================

    radiator = result.get("Radiator", 0)

    if radiator > 0:
        usta += radiator * 500_000

    # =========================
    # 🔥 KATYOL
    # =========================

    if any("katyol" in name.lower() for name in result):
        usta += 1_000_000

    # =========================
    # 🔥 RASSHIRITEL BAK
    # =========================

    if any("rasshiritel bak" in name.lower() for name in result):
        usta += 300_000

    # =========================
    # 🔥 SUVLI TOPLI POL
    # =========================

    if "Penaplast" in result:

        pol = result.get("Pol maydon", 0)

        usta += int(pol * 30_000)

        # kollektor o'rnatish
        usta += 300_000

    # =========================
    # ⚡ KABELLI TOPLI POL
    # =========================

    elif "Isitish kabeli" in result:

        pol = result.get("Pol maydon", 0)

        usta += int(pol * 30_000)

        # datchik o'rnatish
        usta += 200_000

    # =========================
    # 🔥 YAKUNIY
    # =========================

    jami = total + usta

    return total, usta, jami
