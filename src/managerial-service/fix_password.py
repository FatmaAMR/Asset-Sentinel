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
    hashed = pwd.hash('123456')
    print('hash:', hashed)
    r = await db['staff'].update_one(
        {'email': 'mai@sentinel.com'},
        {'$set': {'password': hashed}}
    )
    print('modified:', r.modified_count)
    u = await db['staff'].find_one({'email': 'mai@sentinel.com'}, {'_id': 0})
    print('doc:', u)
    print('verify:', pwd.verify('123456', u['password']))

asyncio.run(go())