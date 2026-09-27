"""
Backup/restore round trip through the real mongodump/mongorestore.

Needs MONGODB_URI in the process env plus the tools, either on PATH or inside a container named
by MONGO_TOOLS_CONTAINER (MONGO_TOOLS_URI = the URI as seen from inside that container).
"""

import json
import os
import shutil
import uuid

import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from db.backup import BackupError, MongoTarget, backup, compare, main, manifest_path, restore, verify


def test_compare_accepts_count_range_and_flags_differences():
    expected = {"a": {"count": [2, 4], "indexes": ["_id_"]}, "b": {"count": 1, "indexes": ["_id_", "x"]}}
    assert compare(expected, {"a": {"count": 3, "indexes": ["_id_"]}, "b": {"count": 1, "indexes": ["_id_", "x"]}}) == []
    problems = compare(expected, {"a": {"count": 5, "indexes": ["_id_"]}, "c": {"count": 0, "indexes": ["_id_"]}})
    assert problems == [
        "a: expected [2, 4] documents, restored 5",
        "b: missing after restore",
        "c: unexpected after restore",
    ]


@pytest.fixture
def target():
    uri = os.environ.get("MONGODB_URI")
    container = os.environ.get("MONGO_TOOLS_CONTAINER")
    if not uri:
        pytest.skip("Set MONGODB_URI in the environment to run backup tests")
    if not container and not (shutil.which("mongodump") and shutil.which("mongorestore")):
        pytest.skip("mongodump/mongorestore not on PATH and MONGO_TOOLS_CONTAINER not set")
    t = MongoTarget(uri, container, os.environ.get("MONGO_TOOLS_URI"))
    try:
        t.client().admin.command("ping")
    except PyMongoError:
        pytest.skip("MongoDB at MONGODB_URI is not reachable")
    return t


@pytest.fixture
def source_db(target):
    name = f"f1ndr_test_bak_{uuid.uuid4().hex[:8]}"
    client = MongoClient(target.uri)
    db = client[name]
    db.users.insert_many([{"email": f"u{i}@example.com", "n": i} for i in range(25)])
    db.users.create_index("email", unique=True, name="users_email_unique")
    db.tokens.insert_one({"jti": "t1", "expires_at": None})
    db.tokens.create_index("expires_at", expireAfterSeconds=0, name="tokens_expires_at_ttl")
    yield db
    for db_name in client.list_database_names():
        if db_name.startswith(name):
            client.drop_database(db_name)
    client.close()


def test_backup_verify_and_restore_round_trip(target, source_db, tmp_path):
    archive = tmp_path / "snap.archive.gz"
    manifest = backup(target, source_db.name, archive)
    assert manifest["collections"]["users"] == {"count": 25, "indexes": ["_id_", "users_email_unique"]}
    assert json.loads(manifest_path(archive).read_text())["sha256"] == manifest["sha256"]

    assert verify(target, archive)["ok"] is True
    client = source_db.client
    assert not [n for n in client.list_database_names() if n.startswith(f"{source_db.name}_verify_")]

    restored = f"{source_db.name}_restored"
    restore(target, archive, restored)
    assert client[restored].users.count_documents({}) == 25
    ttl = client[restored].tokens.index_information()["tokens_expires_at_ttl"]
    assert ttl["expireAfterSeconds"] == 0

    with pytest.raises(BackupError, match="not empty"):
        restore(target, archive, restored)
    client[restored].users.delete_many({})
    restore(target, archive, restored, force=True)
    assert client[restored].users.count_documents({}) == 25


def test_verify_rejects_tampered_archive_and_bad_manifest(target, source_db, tmp_path):
    archive = tmp_path / "snap.archive.gz"
    backup(target, source_db.name, archive)

    manifest = json.loads(manifest_path(archive).read_text())
    manifest["collections"]["users"]["count"] = 26
    manifest_path(archive).write_text(json.dumps(manifest))
    with pytest.raises(BackupError, match="users: expected 26 documents, restored 25"):
        verify(target, archive)

    with open(archive, "ab") as f:
        f.write(b"x")
    with pytest.raises(BackupError, match="Checksum mismatch"):
        verify(target, archive)


def test_cli_backup_and_verify(target, source_db, tmp_path, capsys):
    archive = tmp_path / "cli.archive.gz"
    common = ["--uri", target.uri]
    if target.container:
        common += ["--container", target.container]
    if target.container_uri:
        common += ["--container-uri", target.container_uri]
    assert main([*common, "backup", "--db", source_db.name, "--out", str(archive)]) == 0
    assert main([*common, "verify", "--archive", str(archive)]) == 0
    assert '"ok": true' in capsys.readouterr().out
    assert main([*common, "restore", "--archive", str(archive), "--target-db", source_db.name]) == 1
