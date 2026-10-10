"""Persistence for send-to-phone photo sessions via the shared DocumentStore."""

from db.document_store import DocumentStore

sessions_store = DocumentStore(
    "sellr_photo_sessions",
    key="id",
    indexes=("owner_id", "status", "listing_id"),
    unique=("token_hash",),
)

photos_store = DocumentStore(
    "sellr_photos",
    key="id",
    indexes=("session_id", "owner_id"),
)
