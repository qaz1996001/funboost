import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

loop = asyncio.new_event_loop()
cleint = AsyncIOMotorClient(mongo_collection_string,io_loop=loop)

# Pass this loop to the @boost decorator's specify_async_loop
# =loop