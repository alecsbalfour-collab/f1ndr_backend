"""
Tests for sellr.
"""

from sellr.core.core import create_listing

def test_create_listing():
    data = {"title": "Test", "price": 100}
    result = create_listing(data)
    assert "title" in result
