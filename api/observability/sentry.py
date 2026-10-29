"""Optional Sentry error reporting: no-op unless SENTRY_DSN is set and the SDK
is installed. PII stays off; request_id rides along as a tag."""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_sdk = None


def init_sentry(settings=None) -> bool:
    """Initialize sentry_sdk when configured. Returns whether Sentry is active."""
    global _sdk
    if settings is None:
        from api.config.settings_config import get_settings
        settings = get_settings()
    if not settings.SENTRY_DSN:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logger.warning("SENTRY_DSN set but sentry_sdk not installed; skipping")
        return False
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_COMMIT") or None,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
    )
    _sdk = sentry_sdk
    logger.info("Sentry initialized (env=%s)", settings.ENVIRONMENT)
    return True


def capture(exc: BaseException, request_id: Optional[str] = None) -> None:
    """Report an exception to Sentry with the request_id tag; no-op when off."""
    if _sdk is None:
        return
    with _sdk.push_scope() as scope:
        if request_id:
            scope.set_tag("request_id", request_id)
        _sdk.capture_exception(exc)
