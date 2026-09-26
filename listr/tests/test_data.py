from listr.data.validate_data import VALIDATE_DATA

def test_validate_data_required_fields():
    assert "title" in VALIDATE_DATA["required_fields"]
    assert "body" in VALIDATE_DATA["required_fields"]
