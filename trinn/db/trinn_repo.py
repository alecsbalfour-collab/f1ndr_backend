# f1ndr-backend/trinn/db/trinn_repo.py
"""
Persistence for scheduled trinn tasks via the shared DocumentStore
(Mongo when connected, in-memory otherwise).
"""

from db.document_store import DocumentStore

tasks_store = DocumentStore("trinn_tasks", key="task_id", indexes=("enabled", "status", "task", "listing_id"))
