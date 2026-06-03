from shared.db import Database

from .config import settings

db = Database(settings.database_url)
