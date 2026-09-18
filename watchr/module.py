# f1ndr-backend/watchr/module.py
"""
Watchr module initializer.
Wires repos, services, controllers, and configs.
"""

from watchr.db.mongo_client_watchr import get_watchr_client
from watchr.db.event_log_repo import EventLogRepo
from watchr.db.subscription_repo import SubscriptionRepo
from watchr.db.watcher_state_repo import WatcherStateRepo
from watchr.db.pipeline_repo import PipelineRepo

from watchr.core.service_core import WatchrService
from watchr.core.controller_core import WatchrController

from config.events_config import get_events_config
from config.intervals_config import get_intervals_config
from config.module_settings import get_module_settings
from config.routing_config import get_routing_config
from config.pipeline_config import get_pipeline_config


class WatchrModule:
    def __init__(self, mongo_uri: str):
        self.client = get_watchr_client(mongo_uri)

        # Repos
        self.event_log_repo = EventLogRepo(self.client)
        self.subscription_repo = SubscriptionRepo(self.client)
        self.state_repo = WatcherStateRepo(self.client)
        self.pipeline_repo = PipelineRepo(self.client)

        # Service
        self.service = WatchrService(
            event_log_repo=self.event_log_repo,
            subscription_repo=self.subscription_repo,
            state_repo=self.state_repo,
            pipeline_repo=self.pipeline_repo,
        )

        # Controller
        self.controller = WatchrController(self.service)

        # Configs
        self.events_config = get_events_config()
        self.intervals_config = get_intervals_config()
        self.module_settings = get_module_settings()
        self.routing_config = get_routing_config()
        self.pipeline_config = get_pipeline_config()

    def get_controller(self) -> WatchrController:
        return self.controller
