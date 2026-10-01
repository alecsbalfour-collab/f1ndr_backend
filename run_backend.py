import uvicorn
from api.main import app  # <-- Exposes the app object to Render's root search process
from api.config.settings_config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=None if settings.RELOAD else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
