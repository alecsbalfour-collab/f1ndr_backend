# db/document_store.py
"""
Keyed document storage used by the feature modules.

Uses the shared Mongo database when connected (db.connection_db) and an
in-process dict otherwise, so modules behave the same in tests and local dev.
"""

from copy import deepcopy
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

from pymongo import ASCENDING

from db.connection_db import get_database

_STORES: List["DocumentStore"] = []


class DocumentStore:
    def __init__(self, collection: str, key: str = "id", indexes: Tuple[str, ...] = ()):
        self.collection_name = collection
        self.key = key
        self.indexes = indexes
        self._memory: Dict[Any, dict] = {}
        self._lock = RLock()
        _STORES.append(self)

    @property
    def _collection(self):
        database = get_database()
        return database[self.collection_name] if database is not None else None

    @staticmethod
    def _clean(doc: Optional[dict]) -> Optional[dict]:
        if doc is None:
            return None
        return {k: v for k, v in doc.items() if k != "_id"}

    def _matches(self, doc: dict, query: dict) -> bool:
        return all(doc.get(k) == v for k, v in query.items())

    async def get(self, key: Any) -> Optional[dict]:
        col = self._collection
        if col is not None:
            return self._clean(await col.find_one({self.key: key}))
        with self._lock:
            return deepcopy(self._memory.get(key))

    async def upsert(self, doc: dict) -> bool:
        """Insert or replace by key. Returns True if the document already existed."""
        key = doc[self.key]
        col = self._collection
        if col is not None:
            result = await col.replace_one({self.key: key}, self._clean(doc), upsert=True)
            return result.matched_count > 0
        with self._lock:
            existed = key in self._memory
            self._memory[key] = deepcopy(self._clean(doc))
            return existed

    async def delete(self, key: Any) -> bool:
        col = self._collection
        if col is not None:
            return (await col.delete_one({self.key: key})).deleted_count > 0
        with self._lock:
            return self._memory.pop(key, None) is not None

    async def find(
        self,
        query: Optional[dict] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[Tuple[str, int]] = None,
    ) -> List[dict]:
        query = query or {}
        col = self._collection
        if col is not None:
            cursor = col.find(query).skip(skip).limit(limit)
            if sort:
                cursor = cursor.sort(*sort)
            return [self._clean(d) async for d in cursor]
        with self._lock:
            docs = [deepcopy(d) for d in self._memory.values() if self._matches(d, query)]
        if sort:
            docs.sort(key=lambda d: (d.get(sort[0]) is None, d.get(sort[0])), reverse=sort[1] < 0)
        return docs[skip: skip + limit]

    async def count(self, query: Optional[dict] = None) -> int:
        query = query or {}
        col = self._collection
        if col is not None:
            return await col.count_documents(query)
        with self._lock:
            return sum(1 for d in self._memory.values() if self._matches(d, query))

    async def ensure_indexes(self) -> None:
        col = self._collection
        if col is None:
            return
        await col.create_index([(self.key, ASCENDING)], unique=True, name=f"{self.collection_name}_{self.key}_unique")
        for field in self.indexes:
            await col.create_index([(field, ASCENDING)], name=f"{self.collection_name}_{field}")

    def clear_memory(self) -> None:
        with self._lock:
            self._memory.clear()


async def ensure_all_indexes() -> None:
    for store in _STORES:
        await store.ensure_indexes()
