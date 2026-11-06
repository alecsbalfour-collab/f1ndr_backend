"""Voice engine routes: auth gating, room creation (both domains), turns, prompts."""

import pytest
from fastapi.testclient import TestClient

API = "/api/v1/voice"


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def _force_fallback(monkeypatch):
    """Route responses through the in-process fallback regardless of whether a
    local SquelchGrip engine happens to be running."""
    async def _offline(*args, **kwargs):
        return None
    monkeypatch.setattr("api.routes.voice_routes._remote", _offline)
    monkeypatch.setattr("api.routes.voice_routes._ROOMS", {})


def test_voice_requires_auth(client):
    assert client.post(f"{API}/rooms", json={"room_id": "r1", "initial_topic": "t"}).status_code == 401
    assert client.post(f"{API}/rooms/r1/turns", json={"raw_utterance": "hi"}).status_code == 401
    assert client.get(f"{API}/rooms/r1/prompt").status_code == 401


@pytest.mark.parametrize("domain,lexicon", [("f1ndr", "lex-f1ndr"), ("dealr", "lex-dealr")])
def test_create_room_domains(client, headers_for, domain, lexicon):
    r = client.post(f"{API}/rooms",
                    json={"room_id": f"room-{domain}", "initial_topic": "vehicles", "domain": domain},
                    headers=headers_for("user"))
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["room_id"] == f"room-{domain}"
    assert data["root_node_id"] and data["current_node_id"] == data["root_node_id"]
    assert data["lexicon_pack_ids"] == [lexicon]


def test_turn_normalizes_and_branches(client, headers_for):
    h = headers_for("user", sub="vuser")
    room_id = "room-turns"
    client.post(f"{API}/rooms", json={"room_id": room_id, "initial_topic": "vehicles", "domain": "dealr"}, headers=h)
    r = client.post(f"{API}/rooms/{room_id}/turns",
                    json={"raw_utterance": "Tell me about dealer inventory", "new_tangent_topic": "pricing"},
                    headers=h)
    assert r.status_code == 200, r.text
    turn = r.json()["data"]
    assert turn["resolved_speaker_id"] == "vuser" and turn["speaker_tier"] == "host"
    assert turn["branched_tangent"] is True
    assert "dealr" in turn["normalized_utterance"]


def test_barge_in_detected(client, headers_for):
    h = headers_for("user", sub="vuser2")
    room_id = "room-barge"
    client.post(f"{API}/rooms", json={"room_id": room_id, "initial_topic": "vehicles"}, headers=h)
    r = client.post(f"{API}/rooms/{room_id}/turns", json={"raw_utterance": "wait stop talking"}, headers=h)
    turn = r.json()["data"]
    assert turn["barge_in_command"] and turn["barge_in_action"] == "interrupt"


def test_prompt_aggregates_state(client, headers_for):
    h = headers_for("user", sub="vuser3")
    room_id = "room-prompt"
    client.post(f"{API}/rooms", json={"room_id": room_id, "initial_topic": "vehicles"}, headers=h)
    client.post(f"{API}/rooms/{room_id}/turns",
                json={"raw_utterance": "search for a civic", "new_tangent_topic": "honda pricing"}, headers=h)
    r = client.get(f"{API}/rooms/{room_id}/prompt", headers=h)
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["lineage_breadcrumbs"] == ["vehicles", "honda pricing"]
    assert data["unresolved_tangent_topics"] == ["honda pricing"]
    assert "vehicles" in data["system_prompt_markdown"]


def test_missing_room_404(client, headers_for):
    h = headers_for("user")
    assert client.post(f"{API}/rooms/nope/turns", json={"raw_utterance": "hi"}, headers=h).status_code == 404
    assert client.get(f"{API}/rooms/nope/prompt", headers=h).status_code == 404
