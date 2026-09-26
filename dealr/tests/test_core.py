"""
Tests for dealr.
"""

from dealr.core.core import ingest_inventory

async def test_ingest_inventory():
    data = {"vin": "TESTVIN123"}
    result = await ingest_inventory(data)
    assert "vin" in result
