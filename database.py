import aiosqlite
from config import DATABASE_PATH


# ---------- INIT ----------

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id           INTEGER PRIMARY KEY,
                username          TEXT,
                first_name        TEXT,
                balance           REAL    DEFAULT 0,
                whatsapp          TEXT,
                ref_by            INTEGER,
                affiliate_active  INTEGER DEFAULT 0,
                affiliate_earned  REAL    DEFAULT 0,
                withdraw_password TEXT,
                pix_key           TEXT,
                pix_type          TEXT,
                pix_name          TEXT,
                pix_bank          TEXT,
                gate_message_id   INTEGER,
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def init_products():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                code          TEXT UNIQUE,
                name          TEXT NOT NULL,
                price         REAL NOT NULL,
                old_price     REAL,
                stock         INTEGER DEFAULT 0,
                sold          INTEGER DEFAULT 0,
                description   TEXT,
                guarantee     TEXT,
                category      TEXT,
                active        INTEGER DEFAULT 1,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id  TEXT UNIQUE,
                user_id      INTEGER,
                product_id   INTEGER,
                product_name TEXT,
                price        REAL,
                quantity     INTEGER DEFAULT 1,
                email        TEXT,
                password     TEXT,
                status       TEXT DEFAULT 'active',
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at   TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                txid        TEXT UNIQUE,
                user_id     INTEGER,
                amount      REAL,
                bonus       REAL DEFAULT 0,
                type        TEXT,
                product_id  INTEGER,
                quantity    INTEGER DEFAULT 1,
                status      TEXT DEFAULT 'pending',
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at  TIMESTAMP
            )
        """)
        await db.commit()


async def init_gifts():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS gift_cards (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT UNIQUE NOT NULL,
                value       REAL DEFAULT 0,
                product_id  INTEGER,
                used        INTEGER DEFAULT 0,
                used_by     INTEGER,
                used_at     TIMESTAMP,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


# ---------- USERS ----------

async def get_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()


async def ensure_user(user_id: int, username: str = None, first_name: str = None, ref_by: int = None):
    user = await get_user(user_id)
    if user:
        return user
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO users (user_id, username, first_name, ref_by) VALUES (?,?,?,?)",
            (user_id, username, first_name, ref_by),
        )
        await db.commit()
    return await get_user(user_id)


async def get_balance(user_id: int) -> float:
    user = await get_user(user_id)
    return float(user["balance"]) if user else 0.0


async def add_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
        await db.commit()


async def sub_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id))
        await db.commit()


async def set_gate_message(user_id: int, message_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET gate_message_id=? WHERE user_id=?", (message_id, user_id))
        await db.commit()


async def get_gate_message(user_id: int):
    user = await get_user(user_id)
    return user["gate_message_id"] if user else None


async def update_whatsapp(user_id: int, whatsapp):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET whatsapp=? WHERE user_id=?", (whatsapp, user_id))
        await db.commit()


async def get_user_stats(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        cur = await db.execute(
            "SELECT COUNT(*) as total, COALESCE(SUM(price),0) as gasto "
            "FROM purchases WHERE user_id=?", (user_id,))
        purchases = await cur.fetchone()

        cur = await db.execute(
            "SELECT COALESCE(SUM(amount),0) as total FROM payments "
            "WHERE user_id=? AND status='paid' AND type='topup'", (user_id,))
        pix = await cur.fetchone()

        cur = await db.execute(
            "SELECT COUNT(*) as total FROM gift_cards WHERE used_by=?", (user_id,))
        gifts = await cur.fetchone()

    return {
        "compras": purchases["total"] or 0,
        "gasto": float(purchases["gasto"] or 0),
        "pix": float(pix["total"] or 0),
        "gifts": gifts["total"] or 0,
    }


# ---------- PRODUCTS ----------

async def list_products():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products WHERE active=1 ORDER BY id ASC")
        return await cur.fetchall()


async def get_product(product_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products WHERE id=?", (product_id,))
        return await cur.fetchone()


async def search_products(term: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM products WHERE active=1 AND name LIKE ? ORDER BY id ASC",
            (f"%{term}%",),
        )
        return await cur.fetchall()


async def add_product(code, name, price, old_price=None, stock=0, description="",
                      guarantee="", category=""):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO products (code,name,price,old_price,stock,description,guarantee,category)
               VALUES (?,?,?,?,?,?,?,?)""",
            (code, name, price, old_price, stock, description, guarantee, category),
        )
        await db.commit()


async def remove_product(product_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()


async def set_product_stock(product_id: int, stock: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE products SET stock=? WHERE id=?", (stock, product_id))
        await db.commit()


# ---------- PAYMENTS ----------

async def create_payment(txid, user_id, amount, type_, product_id=None, quantity=1, bonus=0.0):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO payments (txid,user_id,amount,bonus,type,product_id,quantity,status,expires_at)
               VALUES (?,?,?,?,?,?,?, 'pending', datetime('now','+10 minutes'))""",
            (txid, user_id, amount, bonus, type_, product_id, quantity),
        )
        await db.commit()


async def get_payment(txid: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payments WHERE txid=?", (txid,))
        return await cur.fetchone()


async def mark_payment_paid(txid: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE payments SET status='paid' WHERE txid=?", (txid,))
        await db.commit()


# ---------- PURCHASES ----------

async def create_purchase(pid, user_id, product_id, product_name, price, quantity=1, email=None, password=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO purchases (purchase_id,user_id,product_id,product_name,price,quantity,email,password,expires_at)
               VALUES (?,?,?,?,?,?,?,?, datetime('now','+30 days'))""",
            (pid, user_id, product_id, product_name, price, quantity, email, password),
        )
        await db.execute("UPDATE products SET sold = sold + ?, stock = stock - ? WHERE id=?",
                         (quantity, quantity, product_id))
        await db.commit()


async def get_last_purchase(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM purchases WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
        return await cur.fetchone()


async def get_purchase_by_id(purchase_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM purchases WHERE purchase_id=?", (purchase_id,))
        return await cur.fetchone()


async def list_purchases(user_id: int, only_active: bool = False):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if only_active:
            cur = await db.execute(
                "SELECT * FROM purchases WHERE user_id=? AND expires_at > CURRENT_TIMESTAMP "
                "ORDER BY id DESC", (user_id,))
        else:
            cur = await db.execute(
                "SELECT * FROM purchases WHERE user_id=? ORDER BY id DESC", (user_id,))
        return await cur.fetchall()


# ---------- GIFT CARDS ----------

async def get_gift(code: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM gift_cards WHERE code=?", (code,))
        return await cur.fetchone()


async def use_gift(code: str, user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE gift_cards SET used=1, used_by=?, used_at=CURRENT_TIMESTAMP WHERE code=?",
            (user_id, code),
        )
        await db.commit()


async def add_gift(code: str, value: float = 0, product_id: int = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO gift_cards (code, value, product_id) VALUES (?,?,?)",
            (code, value, product_id),
        )
        await db.commit()
