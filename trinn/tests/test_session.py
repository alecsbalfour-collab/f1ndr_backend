"""API tests for trinn chat sessions, mentor teaching, feedback, and tools."""

import pytest
from fastapi.testclient import TestClient

API = "/api/v1"


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean():
    from trinn.db.trinn_repo import memories_store, sessions_store
    from f1ndr.db.db import listings_store
    for s in (memories_store, sessions_store, listings_store):
        s.clear_memory()


def _chat(client, headers, message, **extra):
    return client.post(f"{API}/trinn/chat", json={"message": message, **extra}, headers=headers)


def test_chat_creates_session_and_persists_history(client, headers_for):
    h = headers_for("user", sub="u-chat")
    r = _chat(client, h, "hello trinn")
    assert r.status_code == 200, r.text
    sid = r.json()["data"]["session_id"]
    assert _chat(client, h, "second turn", session_id=sid).status_code == 200
    sess = client.get(f"{API}/trinn/sessions/{sid}", headers=h).json()["data"]
    assert len(sess["messages"]) == 4 and sess["user_id"] == "u-chat"
    assert any(s["id"] == sid for s in client.get(f"{API}/trinn/sessions", headers=h).json()["data"])


def test_session_owner_isolation(client, headers_for):
    sid = _chat(client, headers_for("user", sub="u1"), "hi").json()["data"]["session_id"]
    assert client.get(f"{API}/trinn/sessions/{sid}", headers=headers_for("user", sub="u2")).status_code == 404
    assert client.delete(f"{API}/trinn/sessions/{sid}", headers=headers_for("user", sub="u2")).status_code == 404


def test_mentor_teaching_and_memory_admin(client, headers_for):
    admin = headers_for("admin", sub="founder")
    r = _chat(client, admin, "Lesson: kijiji titles are messy", mode="mentor")
    assert r.status_code == 200 and r.json()["data"]["learned_memory"]["kind"] == "lesson"
    assert _chat(client, headers_for("user"), "x", mode="mentor").status_code == 403
    assert _chat(client, headers_for("user"), "x", teach=True).status_code == 403
    assert client.get(f"{API}/trinn/memories", headers=admin).json()["pagination"]["total"] == 1
    mem_id = r.json()["data"]["learned_memory"]["id"]
    assert client.delete(f"{API}/trinn/memories/{mem_id}", headers=admin).json()["data"]["deleted"]


def test_negative_feedback_creates_correction(client, headers_for):
    admin = headers_for("admin", sub="founder")
    user = headers_for("user", sub="u-fb")
    sid = _chat(client, user, "hi there").json()["data"]["session_id"]
    sess = client.get(f"{API}/trinn/sessions/{sid}", headers=user).json()["data"]
    msg_id = next(m["id"] for m in sess["messages"] if m["role"] == "assistant")
    fb = client.post(f"{API}/trinn/feedback", headers=admin,
                     json={"session_id": sid, "message_id": msg_id,
                           "rating": "down", "correction": "greet users by name"})
    assert fb.status_code == 200
    learned = fb.json()["data"]["learned_memory"]
    assert learned["kind"] == "correction" and learned["weight"] == 8


def test_tools_search_corpus_and_vin(client, headers_for):
    h = headers_for("user")
    r = _chat(client, h, "search listings for a honda")
    assert "search_corpus" in [c["tool"] for c in r.json()["data"]["tool_calls"]]
    r2 = _chat(client, h, "decode VIN 1HGCV1F34LA123456")
    assert "analyze_vehicle" in [c["tool"] for c in r2.json()["data"]["tool_calls"]]


def test_brain_stats(client, headers_for):
    r = client.get(f"{API}/trinn/brain", headers=headers_for("user"))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_memories"] == 0 and data["total_sessions"] == 0
