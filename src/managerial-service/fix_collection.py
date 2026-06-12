import asyncio, os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(dotenv_path=Path('.') / '.env')
client = AsyncIOMotorClient(os.getenv('DB_URL'))
db = client['Asset-Sentinel']

async def go():
    user = await db['staff'].find_one({'email': 'mai@sentinel.com'})
    if not user:
        print('Not found in staff collection')
        return
    user.pop('_id', None)
    existing = await db['managerial_staff'].find_one({'email': 'mai@sentinel.com'})
    if existing:
        await db['managerial_staff'].update_one(
            {'email': 'mai@sentinel.com'},
            {'$set': {'password': user['password'], 'role': 'Admin'}}
        )
        print('Updated in managerial_staff')
    else:
        await db['managerial_staff'].insert_one(user)
        print('Inserted into managerial_staff')

asyncio.run(go())