"""
Tests for sellr.
"""

import pytest

from sellr.core.core import create_listing


async def test_create_listing():
    result = await create_listing({"title": "Test", "price": 100})
    assert result["title"] == "Test"
    assert result["price"] == 100


async def test_create_listing_truncates_title():
    result = await create_listing({"title": "x" * 500, "price": 100})
    assert len(result["title"]) == 120


async def test_create_listing_rejects_negative_price():
    with pytest.raises(ValueError):
        await create_listing({"title": "Test", "price": -1})
