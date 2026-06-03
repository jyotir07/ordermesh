from shared.cache import Cache
from shared.db import Database

from .config import settings

db = Database(settings.database_url)
cache = Cache(settings.redis_url, default_ttl=settings.cache_ttl)
