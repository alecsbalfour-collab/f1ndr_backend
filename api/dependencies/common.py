from fastapi import Depends
from api.config.settings_config import get_settings

def get_app_settings():
    """
    Shared dependency for injecting settings into routes/controllers.
    """
    return get_settings()
