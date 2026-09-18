"""
trinn module entrypoint.
"""

from trinn.core.core import run_task, schedule_task


class TrinnModule:
    def __init__(self):
        self.run_task = run_task
        self.schedule_task = schedule_task
    
    def run(self, action: str, data: dict):
        if action == "run":
            return self.run_task(data)
        if action == "schedule":
            return self.schedule_task(data)
        raise ValueError("Invalid trinn action")
