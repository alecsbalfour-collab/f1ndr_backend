# db/backup.py
"""
MongoDB backup, restore and restore verification built on mongodump/mongorestore.

    python -m db.backup backup  --out backups/f1ndr-20260927.archive.gz
    python -m db.backup verify  --archive backups/f1ndr-20260927.archive.gz
    python -m db.backup restore --archive backups/f1ndr-20260927.archive.gz --target-db f1ndr --force

`backup` writes a gzip archive plus `<archive>.manifest.json` (sha256, per-collection document
counts and index names). `verify` checks the checksum, restores into a throwaway database,
compares it with the manifest and drops it. `restore` refuses a non-empty target without --force
(with --force, restored collections replace existing ones).

Tools run from PATH, or inside a running container with --container (e.g. mongo_main), in which
case --container-uri is the URI as seen from inside that container (defaults to --uri).
--uri/--db default to MONGODB_URI/MONGODB_DB_NAME from settings.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pymongo import MongoClient

MANIFEST_SUFFIX = ".manifest.json"


class BackupError(RuntimeError):
    pass


@dataclass
class MongoTarget:
    uri: str
    container: Optional[str] = None
    container_uri: Optional[str] = None

    def client(self) -> MongoClient:
        return MongoClient(self.uri, serverSelectionTimeoutMS=5000)

    def _command(self, tool: str, args: List[str], stdin_archive: bool) -> tuple:
        """Build the tool command; returns (argv, temp config path or None)."""
        if self.container:
            exec_flags = ["-i"] if stdin_archive else []
            return ["docker", "exec", *exec_flags, self.container, tool, "--uri", self.container_uri or self.uri, *args], None
        if shutil.which(tool) is None:
            raise BackupError(f"{tool} not found on PATH; install MongoDB Database Tools or pass --container")
        # A config file keeps credentials in the URI out of the process list.
        fd, config = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w") as f:
            f.write(f"uri: {json.dumps(self.uri)}\n")
        return [tool, f"--config={config}", *args], config

    def run_tool(self, tool: str, args: List[str], archive: Path, write_archive: bool) -> None:
        argv, config = self._command(tool, args, stdin_archive=not write_archive)
        try:
            with open(archive, "wb" if write_archive else "rb") as f:
                io = {"stdout": f} if write_archive else {"stdin": f, "stdout": subprocess.DEVNULL}
                proc = subprocess.run(argv, stderr=subprocess.PIPE, **io)
        finally:
            if config:
                os.remove(config)
        if proc.returncode != 0:
            stderr = proc.stderr.decode(errors="replace").strip().splitlines()
            raise BackupError(f"{tool} failed ({proc.returncode}): {' | '.join(stderr[-5:])}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(client: MongoClient, db_name: str) -> Dict[str, dict]:
    """Per-collection document count and sorted index names (views and system collections skipped)."""
    db = client[db_name]
    return {
        name: {
            "count": db[name].count_documents({}),
            "indexes": sorted(ix["name"] for ix in db[name].list_indexes()),
        }
        for name in sorted(db.list_collection_names(filter={"type": "collection"}))
        if not name.startswith("system.")
    }


def manifest_path(archive: Path) -> Path:
    return archive.with_name(archive.name + MANIFEST_SUFFIX)


def load_manifest(archive: Path) -> dict:
    path = manifest_path(archive)
    if not path.exists():
        raise BackupError(f"Manifest not found: {path}")
    manifest = json.loads(path.read_text())
    if _sha256(archive) != manifest["sha256"]:
        raise BackupError(f"Checksum mismatch for {archive}; the archive is corrupt or was modified")
    return manifest


def backup(target: MongoTarget, db_name: str, out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    with target.client() as client:
        before = snapshot(client, db_name)
        target.run_tool("mongodump", ["--db", db_name, "--archive", "--gzip"], out, write_archive=True)
        after = snapshot(client, db_name)
    # Writes during the dump can move counts; record the range seen so verify accepts either end.
    collections = {}
    for name, info in after.items():
        counts = sorted({before.get(name, {}).get("count", 0), info["count"]})
        collections[name] = {"count": counts[0] if len(counts) == 1 else counts, "indexes": info["indexes"]}
    manifest = {
        "db": db_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "archive": out.name,
        "sha256": _sha256(out),
        "size_bytes": out.stat().st_size,
        "collections": collections,
    }
    manifest_path(out).write_text(json.dumps(manifest, indent=2))
    return manifest


def restore(target: MongoTarget, archive: Path, target_db: str, force: bool = False) -> dict:
    manifest = load_manifest(archive)
    with target.client() as client:
        if client[target_db].list_collection_names() and not force:
            raise BackupError(f"Target database '{target_db}' is not empty; pass --force to replace its collections")
    args = ["--archive", "--gzip", "--nsFrom", f"{manifest['db']}.*", "--nsTo", f"{target_db}.*", "--drop"]
    target.run_tool("mongorestore", args, archive, write_archive=False)
    return manifest


def compare(expected: Dict[str, dict], actual: Dict[str, dict]) -> List[str]:
    problems = []
    for name in sorted(set(expected) | set(actual)):
        exp, act = expected.get(name), actual.get(name)
        if exp is None or act is None:
            problems.append(f"{name}: {'unexpected' if exp is None else 'missing'} after restore")
            continue
        low, high = exp["count"] if isinstance(exp["count"], list) else (exp["count"], exp["count"])
        if not low <= act["count"] <= high:
            problems.append(f"{name}: expected {exp['count']} documents, restored {act['count']}")
        if exp["indexes"] != act["indexes"]:
            problems.append(f"{name}: expected indexes {exp['indexes']}, restored {act['indexes']}")
    return problems


def verify(target: MongoTarget, archive: Path) -> dict:
    """Restore into a throwaway database, compare with the manifest, then drop it."""
    manifest = load_manifest(archive)
    scratch = f"{manifest['db']}_verify_{uuid.uuid4().hex[:8]}"
    try:
        restore(target, archive, scratch)
        with target.client() as client:
            problems = compare(manifest["collections"], snapshot(client, scratch))
    finally:
        with target.client() as client:
            client.drop_database(scratch)
    if problems:
        raise BackupError("Restore verification failed: " + "; ".join(problems))
    return {"archive": str(archive), "db": manifest["db"], "collections": len(manifest["collections"]), "ok": True}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m db.backup", description=__doc__.split("\n\n")[0])
    parser.add_argument("--uri", help="MongoDB URI (default: MONGODB_URI)")
    parser.add_argument("--container", help="Run mongodump/mongorestore inside this Docker container")
    parser.add_argument("--container-uri", help="URI as seen from inside --container (default: --uri)")
    sub = parser.add_subparsers(dest="command", required=True)
    p_backup = sub.add_parser("backup")
    p_backup.add_argument("--db", help="Database to back up (default: MONGODB_DB_NAME)")
    p_backup.add_argument("--out", type=Path, help="Archive path (default: backups/<db>-<utc timestamp>.archive.gz)")
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--archive", type=Path, required=True)
    p_restore = sub.add_parser("restore")
    p_restore.add_argument("--archive", type=Path, required=True)
    p_restore.add_argument("--target-db", required=True)
    p_restore.add_argument("--force", action="store_true", help="Allow replacing collections in a non-empty target")
    args = parser.parse_args(argv)

    uri, db_name = args.uri, getattr(args, "db", None)
    if uri is None or (args.command == "backup" and db_name is None):
        from api.config.settings_config import get_settings

        settings = get_settings()
        uri, db_name = uri or settings.MONGODB_URI, db_name or settings.MONGODB_DB_NAME
    target = MongoTarget(uri, args.container, args.container_uri)

    try:
        if args.command == "backup":
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            out = args.out or Path("backups") / f"{db_name}-{stamp}.archive.gz"
            manifest = backup(target, db_name, out)
            print(f"Backed up {db_name} ({len(manifest['collections'])} collections) to {out}")
        elif args.command == "verify":
            print(json.dumps(verify(target, args.archive)))
        else:
            restore(target, args.archive, args.target_db, force=args.force)
            print(f"Restored {args.archive} into {args.target_db}")
    except BackupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
