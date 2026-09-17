"""
trinn module entrypoint.
"""

from trinn.core.core import run_task, schedule_task


def run(action: str, data: dict):
    if action == "run":
        return run_task(data)
    if action == "schedule":
        return schedule_task(data)
    raise ValueError("Invalid trinn action")
