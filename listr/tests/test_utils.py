from listr.utils.dict_utils import dict_utils
from listr.utils.post_utils import post_utils
from listr.utils.validation_utils import validation_utils

def test_dict_utils_merge():
    merged = dict_utils.merge({"a": 1}, {"b": 2})
    assert merged == {"a": 1, "b": 2}

def test_post_utils_summarize():
    summary = post_utils.summarize({"title": "T", "body": "Hello World"})
    assert summary["title"] == "T"

def test_validation_utils_missing_fields():
    missing = validation_utils.missing_fields({"title": "X"}, ["title", "body"])
    assert missing == ["body"]
