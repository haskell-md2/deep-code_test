#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, "/app")
os.environ.setdefault("PYTHONPATH", "/app")


async def wait_for_db():
    import asyncpg
    from app.core.config import settings

    dsn = settings.DATABASE_URL.replace("+asyncpg", "")
    for attempt in range(30):
        try:
            conn = await asyncpg.connect(dsn)
            await conn.close()
            print("Database is ready")
            return
        except Exception as e:
            print(f"  Waiting for database... ({attempt+1}/30): {e}")
            await asyncio.sleep(2)
    raise RuntimeError("Database not available after 30 attempts")


async def init_db():

    import app.models.models
    from app.db.database import create_tables
    await create_tables()
    print("Database tables created")


if __name__ == "__main__":
    asyncio.run(wait_for_db())
    asyncio.run(init_db())
    print("Startup complete")