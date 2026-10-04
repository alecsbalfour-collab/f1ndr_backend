# scrapers/db/scrapers_db_connection.py

import motor.motor_asyncio


def get_scrapers_db():
    """
    Return a database handle for scraper modules.

    When the API is running this is the shared connection's database
    (db/connection_db). Standalone callers/tests get their own client on the
    configured URI so this function never silently targets localhost.
    """
    from api.config.settings_config import get_settings
    from db.connection_db import get_database

    database = get_database()
    if database is not None:
        return database
    return motor.motor_asyncio.AsyncIOMotorClient(get_settings().MONGODB_URI)["f1ndr_scrapers"]
