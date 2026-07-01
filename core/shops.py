from math import radians, cos, sin, asin, sqrt


# ================== DISTANCE ==================
def distance_km(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * asin(sqrt(a))

    return R * c


# ================== FIND SHOPS ==================
def find_nearby_shops(
    cursor,
    lat,
    lon,
    radius=10
):

    cursor.execute("""
        SELECT
            user_id,
            name,
            phone,
            lat,
            lon
        FROM users
        WHERE role='dokondor'
    """)

    rows = cursor.fetchall()

    shops = []

    for row in rows:

        user_id, name, phone, shop_lat, shop_lon = row

        # ❌ lokatsiya yo'q
        if shop_lat is None or shop_lon is None:
            continue

        dist = distance_km(
            lat,
            lon,
            shop_lat,
            shop_lon
        )

        # ✅ radius ichida
        if dist <= radius:

            shops.append({
                "user_id": user_id,
                "name": name,
                "phone": phone,
                "distance": round(dist, 1)
            })

    # 🔥 ENG YAQINLAR
    shops.sort(
        key=lambda x: x["distance"]
    )

    return shops
