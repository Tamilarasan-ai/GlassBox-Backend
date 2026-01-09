import asyncio
from app.db.session import get_db
from sqlalchemy import text

async def add_column():
    async for db in get_db():
        try:
            # Try adding the column
            await db.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
            await db.commit()
            print("✅ Added updated_at column")
        except Exception as e:
            print(f"Note: {e}")
            
        # Verify 
        result = await db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sessions'
            ORDER BY ordinal_position
        """))
        print("\nFinal columns:")
        for row in result:
            print(f"  - {row[0]}")
        break

if __name__ == "__main__":
    asyncio.run(add_column())
