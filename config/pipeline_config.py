# f1ndr-backend/watchr/config/pipeline_config.py
"""
Pipeline configuration for Watchr.
"""

def get_pipeline_config() -> dict:
    return {
        "stages": ["event", "subscription", "trigger", "state"],
        "async": True,
    }
