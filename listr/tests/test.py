"""
Tests for listr.
"""

from listr.core.core import push_listing

def test_push_listing():
    listing = {"title": "Test Listing", "price": 100}
    result = push_listing("kijiji", listing)
    assert "title" in result
