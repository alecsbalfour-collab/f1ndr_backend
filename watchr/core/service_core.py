# f1ndr-backend/watchr/core/service_core.py
"""
Watchr service layer.
"""

from watchr.data.event_definitions import build_event_payload
from watchr.data.subscription_data import build_subscription_payload
from watchr.data.trigger_data import build_trigger_payload
from watchr.data.watchr_data import build_state_payload


class WatchrService:
    def __init__(self, event_log_repo, subscription_repo, state_repo, pipeline_repo):
        self.event_log_repo = event_log_repo
        self.subscription_repo = subscription_repo
        self.state_repo = state_repo
        self.pipeline_repo = pipeline_repo

    async def process(self, raw: dict) -> dict:
        event_payload = build_event_payload(raw)
        await self.event_log_repo.insert(event_payload)

        subscription_payload = build_subscription_payload(event_payload)
        await self.subscription_repo.insert(subscription_payload)

        trigger_payload = build_trigger_payload(subscription_payload)
        await self.pipeline_repo.insert(trigger_payload)

        state_payload = build_state_payload(trigger_payload)
        await self.state_repo.insert(state_payload)

        return {
            "event": event_payload,
            "subscription": subscription_payload,
            "trigger": trigger_payload,
            "state": state_payload,
        }
