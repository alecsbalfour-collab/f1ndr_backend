class IntervalsConfig:
    def __init__(self):
        self.HEARTBEAT_INTERVAL_SECONDS = 30
        self.CLEANUP_JOB_INTERVAL_SECONDS = 3600
        self.WATCHDOG_CHECK_INTERVAL_SECONDS = 60

    def defaults(self) -> dict:
        return {
            "heartbeat_interval": 30,
            "watchdog_interval": 60,
            "job_interval": 120,
        }

intervals_config = IntervalsConfig()


def get_intervals_config() -> dict:
    """Watchr-compatible function that returns intervals as dict."""
    return {
        "poll_interval_seconds": 30,
        "max_backoff_seconds": 300,
    }
