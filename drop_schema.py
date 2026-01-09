import asyncio
from app.db.session import get_db
from sqlalchemy import text

async def drop_schema():
    async for db in get_db():
        # Drop in correct order (respect foreign keys)
        await db.execute(text("DROP TABLE IF EXISTS trace_steps CASCADE"))
        await db.execute(text("DROP TABLE IF EXISTS traces CASCADE"))
        await db.execute(text("DROP TABLE IF EXISTS sessions CASCADE"))
        await db.execute(text("DROP TABLE IF EXISTS agents CASCADE"))
        await db.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        await db.commit()
        print("✅ Dropped all tables")
        break

if __name__ == "__main__":
    asyncio.run(drop_schema())
