"""
Tests for listr.
"""

import pytest

from listr.core.core import push_listing, update_listing, remove_listing


async def test_push_listing():
    listing = {"title": "Test Listing", "price": 100}
    result = await push_listing("kijiji", listing)
    assert result["status"] == "pushed"
    assert result["listing"]["title"] == "Test Listing"
    assert result["listing"]["id"]


async def test_push_truncates_title():
    result = await push_listing("ebay", {"title": "x" * 500})
    assert len(result["listing"]["title"]) == 120


async def test_update_then_remove_roundtrip():
    pushed = (await push_listing("craigslist", {"title": "A"}))["listing"]
    assert (await update_listing("craigslist", {**pushed, "title": "B"}))["status"] == "updated"
    assert (await remove_listing("craigslist", pushed))["status"] == "removed"
    assert (await remove_listing("craigslist", pushed))["status"] == "not_found"


async def test_unsupported_platform_rejected():
    with pytest.raises(ValueError):
        await push_listing("myspace", {"title": "A"})
