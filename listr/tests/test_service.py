from listr.core.service_core import ServiceCore

class FakeRepo:
    def create(self, data):
        return {"created": data}

    def get(self, post_id):
        return {"post_id": post_id}


def test_service_create():
    service = ServiceCore(FakeRepo())
    result = service.create_post({"title": "A"})
    assert result["created"]["title"] == "A"


def test_service_get():
    service = ServiceCore(FakeRepo())
    result = service.get_post("999")
    assert result["post_id"] == "999"
