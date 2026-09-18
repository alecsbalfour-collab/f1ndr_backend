# f1ndr-backend/watchr/core/pipeline_core.py
"""
Watchr pipeline engine.
"""

from watchr.data.pipeline_registry import PIPELINE_STAGES


class PipelineCore:
    def __init__(self, repos):
        self.repos = repos

    async def run(self, payload: dict) -> dict:
        result = {}
        current = payload

        for stage in PIPELINE_STAGES:
            repo = self.repos.get(stage)
            current = await repo.process_stage(current)
            result[stage] = current

        return result
