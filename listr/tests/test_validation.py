from listr.core.validation_core import ValidationCore

def test_validation_missing_fields():
    validator = ValidationCore({"required_fields": ["title", "body"]})
    result = validator.validate({"title": "A"})
    assert result["status"] == "error"
    assert "body" in result["missing_fields"]

def test_validation_ok():
    validator = ValidationCore({"required_fields": ["title", "body"]})
    result = validator.validate({"title": "A", "body": "B"})
    assert result["status"] == "ok"
