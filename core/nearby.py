from core.location import calculate_distance


def find_nearby_masters(cursor, lat, lon, radius=10):

    cursor.execute("""
        SELECT user_id, name, phone, lat, lon, rating
        FROM users
        WHERE role='usta'
        AND is_online=1
    """)

    users = cursor.fetchall()

    nearby = []

    for user in users:

        user_id, name, phone, u_lat, u_lon, rating = user

        if not u_lat or not u_lon:
            continue

        distance = calculate_distance(
            lat,
            lon,
            u_lat,
            u_lon
        )

        if distance <= radius:

            nearby.append({
                "user_id": user_id,
                "name": name,
                "phone": phone,
                "distance": round(distance, 1),
                "rating": rating
            })

    # 🔥 YAQINLAR BIRINCHI
    nearby.sort(key=lambda x: x["distance"])

    return nearby
