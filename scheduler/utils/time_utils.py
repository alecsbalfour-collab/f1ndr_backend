from datetime import datetime, timezone

class TimeUtils:
    def now(self):
        return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


time_utils = TimeUtils()
