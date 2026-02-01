import os
from motor.motor_asyncio import AsyncIOMotorClient

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI não encontrado no ambiente (.env)")
        _client = AsyncIOMotorClient(uri)
    return _client


def get_db():
    client = get_client()
    return client.get_default_database()
