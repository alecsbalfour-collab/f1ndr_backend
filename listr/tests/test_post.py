from listr.data.post_data import POST_DATA

def test_post_data_fields():
    assert "title" in POST_DATA["fields"]
    assert "body" in POST_DATA["fields"]
