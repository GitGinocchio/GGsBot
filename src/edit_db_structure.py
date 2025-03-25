from dotenv import load_dotenv
import asyncio

load_dotenv('./config/.env', verbose=True)

from utils.db import Database

db = Database()

async def main():
    async with db:
        await db.executeScript("""ALTER TABLE users DROP COLUMN level;""",autocommit=True)
        await db.executeScript("""ALTER TABLE users ADD COLUMN level INTEGER;""",autocommit=True)


if __name__ == "__main__":
    asyncio.run(main())
