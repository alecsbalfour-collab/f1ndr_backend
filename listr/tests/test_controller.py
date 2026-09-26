from listr.core.controller_core import ControllerCore
from listr.core.service_core import ServiceCore
from listr.core.validation_core import ValidationCore


class FakeRepo:
    def create(self, data):
        return {"created": data}

    def get(self, post_id):
        return {"post_id": post_id}


def _controller():
    return ControllerCore(ServiceCore(FakeRepo()), ValidationCore({"required_fields": ["title", "body"]}))


def test_controller_create_valid():
    result = _controller().create_post({"title": "A", "body": "B"})
    assert result["created"]["title"] == "A"


def test_controller_create_invalid_returns_validation_error():
    result = _controller().create_post({"title": "A"})
    assert result["status"] == "error"
    assert result["missing_fields"] == ["body"]


def test_controller_get():
    assert _controller().get_post("7")["post_id"] == "7"
