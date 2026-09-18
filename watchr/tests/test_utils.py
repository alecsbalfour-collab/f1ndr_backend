# f1ndr-backend/watchr/tests/test_utils.py
from watchr.utils.dict_utils import merge_dicts


def test_merge_dicts():
    assert merge_dicts({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
