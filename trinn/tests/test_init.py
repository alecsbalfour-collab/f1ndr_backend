# f1ndr-backend/trinn/tests/test_init.py
from trinn import TrinnModule, get_trinn_config


def test_trinn_init():
    module = TrinnModule()
    assert module.config["feature_key"] == "trinn"
    assert get_trinn_config()["enabled"] is True
