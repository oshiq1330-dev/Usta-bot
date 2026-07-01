import sqlite3

conn = sqlite3.connect(
    "data.db",
    check_same_thread=False,
    timeout=30
)

cursor = conn.cursor()

# ================= USERS =================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    user_id INTEGER PRIMARY KEY,

    role TEXT,

    name TEXT,

    phone TEXT,

    lat REAL,

    lon REAL,

    rating REAL DEFAULT 5,

    rating_count INTEGER DEFAULT 0,

    last_location_update TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# 🔥 SHOP STATS
try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN shop_rating REAL DEFAULT 5
    """)
except:
    pass

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN shop_sales INTEGER DEFAULT 0
    """)
except:
    pass

conn.commit()

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN shop_rating_count INTEGER DEFAULT 0
    """)
except:
    pass

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN is_online INTEGER DEFAULT 0
    """)
except:
    pass

conn.commit()

# ================= REQUESTS =================

cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    client_id INTEGER,

    problem TEXT,

    lat REAL,

    lon REAL,

    status TEXT DEFAULT 'new',

    accepted_by INTEGER DEFAULT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# ================= PRODUCT REQUESTS =================

cursor.execute("""
CREATE TABLE IF NOT EXISTS product_requests (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    master_id INTEGER,

    shop_id INTEGER,

    product_name TEXT,

    price TEXT,

    status TEXT DEFAULT 'new',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

