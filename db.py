import aiosqlite
from config import DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                free_used   INTEGER NOT NULL DEFAULT 0,
                total_paid  INTEGER NOT NULL DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_user(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            # Авто-создание при первом обращении
            await db.execute(
                "INSERT INTO users (user_id) VALUES (?)", (user_id,)
            )
            await db.commit()
            return {"user_id": user_id, "free_used": 0, "total_paid": 0}


async def increment_free(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET free_used = free_used + 1 WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()


async def increment_paid(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_paid = total_paid + 1 WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()
