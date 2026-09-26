"""
Tests for listr.
"""

import pytest

from listr.core.core import push_listing, update_listing, remove_listing


def test_push_listing():
    listing = {"title": "Test Listing", "price": 100}
    result = push_listing("kijiji", listing)
    assert result["status"] == "pushed"
    assert result["listing"]["title"] == "Test Listing"
    assert result["listing"]["id"]


def test_push_truncates_title():
    result = push_listing("ebay", {"title": "x" * 500})
    assert len(result["listing"]["title"]) == 120


def test_update_then_remove_roundtrip():
    pushed = push_listing("facebook", {"title": "A"})["listing"]
    assert update_listing("facebook", {**pushed, "title": "B"})["status"] == "updated"
    assert remove_listing("facebook", pushed)["status"] == "removed"
    assert remove_listing("facebook", pushed)["status"] == "not_found"


def test_unsupported_platform_rejected():
    with pytest.raises(ValueError):
        push_listing("myspace", {"title": "A"})
