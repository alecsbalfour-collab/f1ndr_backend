# db/document_store.py
"""
Keyed document storage used by the feature modules.

Uses the shared Mongo database when connected (db.connection_db) and an
in-process dict otherwise, so modules behave the same in tests and local dev.
"""

from copy import deepcopy
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

from pymongo import ASCENDING, ReturnDocument

from db.connection_db import get_database

_STORES: List["DocumentStore"] = []


class DocumentStore:
    def __init__(
        self,
        collection: str,
        key: str = "id",
        indexes: Tuple[str, ...] = (),
        unique: Tuple[str, ...] = (),
        ttl_field: Optional[str] = None,
    ):
        """`ttl_field` must hold a naive-UTC datetime; Mongo deletes the doc once it passes."""
        self.collection_name = collection
        self.key = key
        self.indexes = indexes
        self.unique = unique
        self.ttl_field = ttl_field
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

    async def update(self, key: Any, fields: dict) -> bool:
        """Set the given fields on an existing document. Returns True if it existed."""
        col = self._collection
        if col is not None:
            return (await col.update_one({self.key: key}, {"$set": fields})).matched_count > 0
        with self._lock:
            if key not in self._memory:
                return False
            self._memory[key].update(deepcopy(fields))
            return True

    async def increment(self, key: Any, field: str, amount: int = 1) -> Optional[int]:
        """Atomically add to a numeric field; returns the new value, or None if the doc is missing."""
        col = self._collection
        if col is not None:
            doc = await col.find_one_and_update(
                {self.key: key}, {"$inc": {field: amount}}, return_document=ReturnDocument.AFTER
            )
            return None if doc is None else doc[field]
        with self._lock:
            doc = self._memory.get(key)
            if doc is None:
                return None
            doc[field] = doc.get(field, 0) + amount
            return doc[field]

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
        for field in self.unique:
            await col.create_index([(field, ASCENDING)], unique=True, name=f"{self.collection_name}_{field}_unique")
        if self.ttl_field:
            await col.create_index(
                [(self.ttl_field, ASCENDING)], expireAfterSeconds=0, name=f"{self.collection_name}_{self.ttl_field}_ttl"
            )

    def clear_memory(self) -> None:
        with self._lock:
            self._memory.clear()


async def ensure_all_indexes() -> None:
    for store in _STORES:
        await store.ensure_indexes()
