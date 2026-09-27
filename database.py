import aiosqlite
from config import DATABASE_PATH

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


async def set_gate_message(user_id: int, message_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET gate_message_id=? WHERE user_id=?", (message_id, user_id))
        await db.commit()


async def get_gate_message(user_id: int):
    user = await get_user(user_id)
    return user["gate_message_id"] if user else None
