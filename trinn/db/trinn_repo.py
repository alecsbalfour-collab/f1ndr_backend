# f1ndr-backend/trinn/db/trinn_repo.py
"""
Persistence for scheduled trinn tasks via the shared DocumentStore
(Mongo when connected, in-memory otherwise).
"""

from db.document_store import DocumentStore

tasks_store = DocumentStore("trinn_tasks", key="task_id", indexes=("enabled", "status", "task", "listing_id"))

# Trinn's long-term brain: taught lessons/facts/preferences (memory_core) and
# multi-turn chat sessions (agent_core).
memories_store = DocumentStore("trinn_memories", key="id", indexes=("topic", "kind", "author_id"))
sessions_store = DocumentStore("trinn_sessions", key="id", indexes=("user_id",))
