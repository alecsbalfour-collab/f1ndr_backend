"""
Tests for trinn.
"""

from trinn.core.core import run_task

def test_run_task():
    data = {"task": "scrape", "platform": "kijiji"}
    result = run_task(data)
    assert result is not None
