"""Trinn long-term memory: lessons the founder teaches it, recalled to ground
answers. In-memory/Mongo via the shared DocumentStore."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from trinn.db.trinn_repo import memories_store

KINDS = {"lesson", "correction", "fact", "preference"}
TOPICS = {"general", "pricing", "fraud", "vehicles", "rvs", "copywriting", "operations"}


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def _tokens(text: str) -> set:
    return {t for t in "".join(c if c.isalnum() else " " for c in (text or "").lower()).split() if len(t) > 2}


async def teach_memory(data: Dict, author_id: Optional[str]) -> Dict:
    """Persist a taught rule/insight. `data`: kind, topic, content, context?, weight?"""
    now = _utcnow()
    memory = {
        "id": data.get("id") or uuid.uuid4().hex[:12],
        "kind": data.get("kind") or "lesson",
        "topic": data.get("topic") or "general",
        "content": data["content"],
        "context": data.get("context"),
        "weight": max(1, min(10, int(data.get("weight") or 5))),
        "author_id": author_id,
        "use_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    await memories_store.upsert(memory)
    return memory


async def list_memories(topic: Optional[str] = None, kind: Optional[str] = None,
                        page: int = 1, page_size: int = 50) -> Dict:
    query = {k: v for k, v in {"topic": topic, "kind": kind}.items() if v}
    docs = await memories_store.find(query, limit=10_000)
    docs.sort(key=lambda d: d.get("created_at") or "", reverse=True)
    total = len(docs)
    return {"total": total, "items": docs[(page - 1) * page_size: page * page_size]}


async def delete_memory(memory_id: str) -> bool:
    return bool(await memories_store.delete(memory_id))


async def recall_memories(prompt: str, topic: Optional[str] = None, limit: int = 8) -> List[Dict]:
    """Rank memories for a prompt: topic bonus + token overlap + weight.
    Recalled memories get use_count incremented."""
    docs = await memories_store.find({"topic": topic} if topic else {}, limit=10_000)
    if not docs:
        return []
    prompt_tokens = _tokens(prompt)
    scored = []
    for doc in docs:
        overlap = len(prompt_tokens & _tokens(" ".join(str(doc.get(f) or "") for f in ("content", "context", "topic"))))
        score = overlap * 2 + (doc.get("weight") or 5) + (5 if topic and doc.get("topic") == topic else 0)
        if overlap or topic:
            scored.append((score, doc))
    scored.sort(key=lambda t: t[0], reverse=True)
    recalled = []
    for _, doc in scored[:limit]:
        doc["use_count"] = (doc.get("use_count") or 0) + 1
        await memories_store.upsert(doc)
        recalled.append(doc)
    return recalled


async def bump_weight(memory_id: str, delta: int) -> None:
    doc = await memories_store.get(memory_id)
    if doc:
        doc["weight"] = max(1, min(10, (doc.get("weight") or 5) + delta))
        doc["updated_at"] = _utcnow()
        await memories_store.upsert(doc)


async def brain_stats() -> Dict:
    docs = await memories_store.find({}, limit=10_000)
    by_topic: Dict[str, int] = {}
    recalls = 0
    for d in docs:
        by_topic[d.get("topic") or "general"] = by_topic.get(d.get("topic") or "general", 0) + 1
        recalls += d.get("use_count") or 0
    return {"total_memories": len(docs), "memories_by_topic": by_topic, "total_recalls": recalls}
