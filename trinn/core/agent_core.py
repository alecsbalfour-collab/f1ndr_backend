"""Trinn's agent brain: multi-turn chat sessions, ecosystem tool use, mentor
teaching, feedback-driven learning, and optional LLM completion."""

import re
import uuid
from datetime import datetime, timezone
from statistics import median
from typing import Any, Dict, List, Optional

from trinn.db.trinn_repo import sessions_store
from trinn.core.memory_core import brain_stats, bump_weight, recall_memories, teach_memory

TEACH_PREFIX = re.compile(r"^\s*(remember|lesson|rule|note)\s*:", re.I)


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def _msg(role: str, content: str, **extra) -> Dict:
    return {"id": uuid.uuid4().hex[:10], "role": role, "content": content,
            "timestamp": _utcnow(), **extra}


# ---------------- sessions ----------------

async def create_session(user_id: str, mode: str = "assistant", title: Optional[str] = None) -> Dict:
    now = _utcnow()
    session = {"id": uuid.uuid4().hex[:12], "user_id": user_id, "mode": mode,
               "title": title, "messages": [], "created_at": now, "updated_at": now}
    await sessions_store.upsert(session)
    return session


async def get_session(session_id: str) -> Optional[Dict]:
    return await sessions_store.get(session_id)


async def list_sessions(user_id: str) -> List[Dict]:
    docs = await sessions_store.find({"user_id": user_id}, limit=10_000)
    return sorted(docs, key=lambda d: d.get("updated_at") or "", reverse=True)


async def delete_session(session_id: str) -> bool:
    return bool(await sessions_store.delete(session_id))


# ---------------- tools ----------------

async def tool_search_corpus(query: str) -> Dict:
    from f1ndr.core.core import run_search
    result = await run_search({"query": query})
    listings = result.get("results", [])
    prices = [l["price"] for l in listings if isinstance(l.get("price"), (int, float))]
    return {
        "tool": "search_corpus", "query": query, "count": len(listings),
        "min_price": min(prices) if prices else None,
        "median_price": median(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "top": [{"title": l.get("title"), "price": l.get("price"),
                 "platform": l.get("platform"), "url": l.get("url")} for l in listings[:5]],
    }


async def tool_compare_listings(query: str) -> Dict:
    from f1ndr.core.core import query_listings
    from f1ndr.utils.utils import group_equivalent_listings
    docs = await query_listings({})
    groups = group_equivalent_listings(docs)
    top = sorted(groups, key=lambda g: (g.get("price_spread") or 0), reverse=True)[:5]
    return {"tool": "compare_listings", "groups": len(groups), "top_spreads": top}


async def tool_analyze_vehicle(vin: str) -> Dict:
    from f1ndr.core.core import run_intelligence
    return {"tool": "analyze_vehicle", "vin": vin,
            "analysis": await run_intelligence({"vin": vin})}


async def tool_system_status() -> Dict:
    from scrapers.module import health_report
    from trinn.utils.scheduler import get_scheduler_state
    return {"tool": "system_status", "scrapers": health_report(),
            "scheduler": get_scheduler_state()}


_VIN = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.I)


async def _run_tools(message: str) -> List[Dict]:
    """Keyword/VIN tool routing; each call is isolated so a tool failure can't break chat."""
    text = message.lower()
    calls: List[Dict] = []
    try:
        if "status" in text and ("system" in text or "scraper" in text or "scheduler" in text or "health" in text):
            calls.append(await tool_system_status())
        m = _VIN.search(message)
        if m:
            calls.append(await tool_analyze_vehicle(m.group(0).upper()))
        if "compare" in text or "price spread" in text or "same listing" in text:
            calls.append(await tool_compare_listings(message))
        if any(k in text for k in ("search", "find", "show me", "listings", "price", "for sale")) \
                and not calls:
            calls.append(await tool_search_corpus(message))
    except Exception as e:  # tools must never fail the chat itself
        calls.append({"tool": "error", "error": str(e)})
    return calls


# ---------------- llm ----------------

def _llm_settings():
    from trinn.config.config import get_trinn_config
    cfg = get_trinn_config()
    return cfg.get("llm_url"), cfg.get("llm_api_key"), cfg.get("llm_model")


async def _llm_reply(system: str, history: List[Dict]) -> Optional[str]:
    url, api_key, model = _llm_settings()
    if not url:
        return None
    try:
        import httpx
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        if "anthropic" in url:
            r = await httpx.AsyncClient(timeout=30).post(
                f"{url.rstrip('/')}/v1/messages",
                headers={**headers, "anthropic-version": "2023-06-01"},
                json={"model": model or "claude-sonnet-4-6", "max_tokens": 1024,
                      "system": system,
                      "messages": [{"role": m["role"], "content": m["content"]} for m in history[-10:]]})
            r.raise_for_status()
            return r.json()["content"][0]["text"]
        r = await httpx.AsyncClient(timeout=30).post(
            f"{url.rstrip('/')}/v1/chat/completions", headers=headers,
            json={"model": model or "gpt-4o-mini",
                  "messages": [{"role": "system", "content": system}] +
                              [{"role": m["role"], "content": m["content"]} for m in history[-10:]]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return None


def _synthesize(message: str, tool_calls: List[Dict], memories: List[Dict], learned: Optional[Dict]) -> str:
    parts = []
    if learned:
        parts.append(f"Got it — I've learned that ({learned['kind']}, topic: {learned['topic']}, weight {learned['weight']}).")
    for call in tool_calls:
        if call.get("tool") == "search_corpus":
            parts.append(f"Corpus search found {call['count']} listings"
                         + (f" (prices {call['min_price']}–{call['max_price']}, median {call['median_price']})." if call["count"] else "."))
            for t in call["top"][:3]:
                parts.append(f"- {t['title']} — {t['price']} ({t['platform']})")
        elif call.get("tool") == "compare_listings":
            parts.append(f"{call['groups']} comparison groups across platforms.")
        elif call.get("tool") == "analyze_vehicle":
            parts.append(f"VIN analysis: {call['analysis']}")
        elif call.get("tool") == "system_status":
            parts.append(f"System: scrapers {call['scrapers']['status']}, scheduler running={call['scheduler'].get('running')}.")
    if memories:
        parts.append(f"({len(memories)} memor{'y' if len(memories) == 1 else 'ies'} applied.)")
    return "\n".join(parts) or "Understood. Ask me about listings, prices, VINs, or system status — or teach me with 'Lesson: ...'."


# ---------------- chat + feedback ----------------

async def chat(user_id: str, message: str, session_id: Optional[str] = None,
               mode: str = "assistant", teach: bool = False,
               is_admin: bool = False) -> Dict:
    session = await get_session(session_id) if session_id else None
    if session is None:
        session = await create_session(user_id, mode)
    if not session.get("title"):
        session["title"] = message[:60]

    learned = None
    if is_admin and (teach or TEACH_PREFIX.match(message)):
        content = TEACH_PREFIX.sub("", message).strip() or message
        learned = await teach_memory({"content": content, "kind": "lesson"}, author_id=user_id)

    memories = await recall_memories(message)
    tool_calls = await _run_tools(message)

    session["messages"].append(_msg("user", message))
    system = (
        "You are Trinn, the f1ndr assistant. Ground answers in these lessons and tool results.\n"
        + "\n".join(f"- [{m['kind']}/{m['topic']}] {m['content']}" for m in memories)
    )
    reply = await _llm_reply(system, session["messages"])
    if reply is None:
        reply = _synthesize(message, tool_calls, memories, learned)
    session["messages"].append(_msg("assistant", reply, tool_calls=[c.get("tool") for c in tool_calls],
                                    memories_used=[m["id"] for m in memories]))
    session["updated_at"] = _utcnow()
    await sessions_store.upsert(session)

    return {"session_id": session["id"], "reply": reply, "tool_calls": tool_calls,
            "memories_used": memories, "learned_memory": learned}


async def record_feedback(session_id: str, message_id: str, rating: str,
                          correction: Optional[str], author_id: str) -> Optional[Dict]:
    session = await get_session(session_id)
    if not session:
        return None
    message = next((m for m in session["messages"] if m["id"] == message_id), None)
    if not message:
        return None
    learned = None
    if rating == "up":
        for mid in message.get("memories_used") or []:
            await bump_weight(mid, 1)
    elif rating == "down" and correction:
        learned = await teach_memory({"content": correction, "kind": "correction",
                                      "weight": 8}, author_id=author_id)
    message["feedback"] = rating
    session["updated_at"] = _utcnow()
    await sessions_store.upsert(session)
    return {"recorded": True, "learned_memory": learned}


async def brain_overview() -> Dict:
    stats = await brain_stats()
    sessions = await sessions_store.find({}, limit=10_000)
    url, _, _ = _llm_settings()
    provider = "anthropic" if url and "anthropic" in url else "openai-compatible" if url else None
    return {**stats, "total_sessions": len(sessions), "llm_provider": provider}
