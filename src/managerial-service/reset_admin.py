import asyncio, os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

load_dotenv(dotenv_path=Path('.') / '.env')
client = AsyncIOMotorClient(os.getenv('DB_URL'))
db = client['Asset-Sentinel']
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def go():
    r = await db['staff'].update_one(
        {'email': 'mai@sentinel.com'},
        {'$set': {'password': pwd.hash('123456'), 'role': 'Admin'}}
    )
    print('modified:', r.modified_count)

asyncio.run(go())