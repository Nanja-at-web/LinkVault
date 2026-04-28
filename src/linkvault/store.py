from __future__ import annotations

import base64
import csv
import io
import json
import sqlite3
import struct
import zipfile
from hashlib import sha256
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import urlsplit
from uuid import uuid4

from .metadata import PageMetadata, check_url_health, fetch_url_metadata
from .url_tools import normalize_url


def _safe_json(s: str, default: Any) -> Any:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default


@dataclass
class Bookmark:
    id: str
    url: str
    normalized_url: str
    title: str
    description: str = ""
    domain: str = ""
    favicon_url: str = ""
    tags: list[str] = field(default_factory=list)
    collections: list[str] = field(default_factory=list)
    favorite: bool = False
    pinned: bool = False
    notes: str = ""
    status: str = "active"
    merged_into: str = ""
    merged_at: str = ""
    source_browser: str = ""
    source_root: str = ""
    source_folder_path: str = ""
    source_position: int = -1
    source_bookmark_id: str = ""
    archive_status: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


BOOKMARK_SORT_FIELDS = {"created_at", "updated_at", "title", "domain"}
BOOKMARK_SORT_ORDERS = {"asc", "desc"}


@dataclass
class BookmarkFilters:
    favorite: bool | None = None
    pinned: bool | None = None
    domain: str = ""
    tag: str = ""
    collection: str = ""
    status: str = "active"
    sort_by: str = "created_at"
    sort_order: str = "desc"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImportSession:
    id: str
    source_name: str
    source_format: str
    source_file_name: str = ""
    source_file_checksum_sha256: str = ""
    source_profile: str = ""
    sync_origin: str = ""
    imported_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    created_count: int = 0
    duplicate_count: int = 0
    conflict_count: int = 0
    invalid_count: int = 0
    raw_summary_json: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["summary"] = _safe_json(self.raw_summary_json, {})
        return payload


@dataclass
class RestoreSession:
    id: str
    source_name: str
    target_mode: str
    target_folder_id: str = ""
    target_title: str = ""
    query: str = ""
    filters_json: str = "{}"
    duplicate_action: str = "skip_existing"
    total_count: int = 0
    create_count: int = 0
    skip_existing_count: int = 0
    merge_existing_count: int = 0
    update_existing_count: int = 0
    conflict_count: int = 0
    structure_conflict_count: int = 0
    decision_count: int = 0
    state: str = "previewed"
    result_json: str = "{}"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["filters"] = _safe_json(self.filters_json, {})
        payload["result"] = _safe_json(self.result_json, {})
        return payload


@dataclass
class ActivityEvent:
    id: str
    kind: str
    object_type: str
    object_id: str
    summary: str
    details_json: str = "{}"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["details"] = _safe_json(self.details_json, {})
        return payload


@dataclass
class ConflictRecord:
    id: str
    kind: str
    source_type: str
    source_id: str
    state: str = "open"
    summary: str = ""
    details_json: str = "{}"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    resolved_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["details"] = _safe_json(self.details_json, {})
        return payload


@dataclass
class StoredSetting:
    key: str
    value_json: str
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": _safe_json(self.value_json, None),
            "updated_at": self.updated_at,
        }


MetadataFetcher = Callable[[str], PageMetadata]


class BookmarkStore:
    def __init__(self, path: Path, metadata_fetcher: MetadataFetcher | None = fetch_url_metadata) -> None:
        self.path = path
        self.metadata_fetcher = metadata_fetcher
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    normalized_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    domain TEXT NOT NULL DEFAULT '',
                    favicon_url TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT '',
                    collections TEXT NOT NULL DEFAULT '',
                    favorite INTEGER NOT NULL DEFAULT 0,
                    pinned INTEGER NOT NULL DEFAULT 0,
                    notes TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active',
                    merged_into TEXT NOT NULL DEFAULT '',
                    merged_at TEXT NOT NULL DEFAULT '',
                    source_browser TEXT NOT NULL DEFAULT '',
                    source_root TEXT NOT NULL DEFAULT '',
                    source_folder_path TEXT NOT NULL DEFAULT '',
                    source_position INTEGER NOT NULL DEFAULT -1,
                    source_bookmark_id TEXT NOT NULL DEFAULT '',
                    archive_status TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            ensure_column(connection, "bookmarks", "description", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "domain", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "favicon_url", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "status", "TEXT NOT NULL DEFAULT 'active'")
            ensure_column(connection, "bookmarks", "merged_into", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "merged_at", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "source_browser", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "source_root", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "source_folder_path", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "source_position", "INTEGER NOT NULL DEFAULT -1")
            ensure_column(connection, "bookmarks", "source_bookmark_id", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "bookmarks", "archive_status", "TEXT NOT NULL DEFAULT ''")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_normalized_url ON bookmarks(normalized_url)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_domain ON bookmarks(domain)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_status ON bookmarks(status)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_source_root ON bookmarks(source_root)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS merge_events (
                    id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    winner_id TEXT NOT NULL,
                    loser_ids TEXT NOT NULL,
                    winner_before_json TEXT NOT NULL,
                    losers_before_json TEXT NOT NULL,
                    winner_after_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    undone_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            ensure_column(connection, "merge_events", "undone_at", "TEXT NOT NULL DEFAULT ''")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_merge_events_winner_id ON merge_events(winner_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_merge_events_created_at ON merge_events(created_at)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS import_sessions (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    source_format TEXT NOT NULL,
                    source_file_name TEXT NOT NULL DEFAULT '',
                    source_file_checksum_sha256 TEXT NOT NULL DEFAULT '',
                    source_profile TEXT NOT NULL DEFAULT '',
                    sync_origin TEXT NOT NULL DEFAULT '',
                    imported_at TEXT NOT NULL,
                    created_count INTEGER NOT NULL DEFAULT 0,
                    duplicate_count INTEGER NOT NULL DEFAULT 0,
                    conflict_count INTEGER NOT NULL DEFAULT 0,
                    invalid_count INTEGER NOT NULL DEFAULT 0,
                    raw_summary_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS import_records (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    item_id TEXT NOT NULL DEFAULT '',
                    source_browser TEXT NOT NULL DEFAULT '',
                    source_path TEXT NOT NULL DEFAULT '',
                    source_id TEXT NOT NULL DEFAULT '',
                    url_raw TEXT NOT NULL DEFAULT '',
                    url_normalized TEXT NOT NULL DEFAULT '',
                    action TEXT NOT NULL,
                    raw_payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES import_sessions(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_import_sessions_imported_at ON import_sessions(imported_at)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_import_records_session_id ON import_records(session_id)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_events (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    object_type TEXT NOT NULL,
                    object_id TEXT NOT NULL DEFAULT '',
                    summary TEXT NOT NULL,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_created_at ON activity_events(created_at)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_kind ON activity_events(kind)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS restore_sessions (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    target_mode TEXT NOT NULL,
                    target_folder_id TEXT NOT NULL DEFAULT '',
                    target_title TEXT NOT NULL DEFAULT '',
                    query TEXT NOT NULL DEFAULT '',
                    filters_json TEXT NOT NULL DEFAULT '{}',
                    duplicate_action TEXT NOT NULL DEFAULT 'skip_existing',
                    total_count INTEGER NOT NULL DEFAULT 0,
                    create_count INTEGER NOT NULL DEFAULT 0,
                    skip_existing_count INTEGER NOT NULL DEFAULT 0,
                    merge_existing_count INTEGER NOT NULL DEFAULT 0,
                    update_existing_count INTEGER NOT NULL DEFAULT 0,
                    conflict_count INTEGER NOT NULL DEFAULT 0,
                    structure_conflict_count INTEGER NOT NULL DEFAULT 0,
                    decision_count INTEGER NOT NULL DEFAULT 0,
                    state TEXT NOT NULL DEFAULT 'previewed',
                    result_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_restore_sessions_created_at ON restore_sessions(created_at DESC)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_restore_sessions_state ON restore_sessions(state)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conflicts (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT 'open',
                    summary TEXT NOT NULL DEFAULT '',
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    resolved_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            ensure_column(connection, "conflicts", "summary", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "conflicts", "updated_at", "TEXT NOT NULL DEFAULT ''")
            ensure_column(connection, "conflicts", "resolved_at", "TEXT NOT NULL DEFAULT ''")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_created_at ON conflicts(created_at DESC)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_state ON conflicts(state)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_kind ON conflicts(kind)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, key)
                )
                """
            )
            # Migrate old single-key schema (no user_id column) to per-user schema
            old_cols = {row["name"] for row in connection.execute("PRAGMA table_info(user_settings)")}
            if "user_id" not in old_cols:
                # Drop leftover temp table from any previously interrupted migration
                connection.execute("DROP TABLE IF EXISTS user_settings_new")
                connection.execute(
                    """
                    CREATE TABLE user_settings_new (
                        user_id TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value_json TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (user_id, key)
                    )
                    """
                )
                users_table = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
                ).fetchone()
                if users_table:
                    try:
                        first_admin = connection.execute(
                            "SELECT id FROM users WHERE role = 'admin' ORDER BY created_at ASC LIMIT 1"
                        ).fetchone()
                    except sqlite3.OperationalError:
                        # role column not yet added by AuthStore.migrate() —
                        # fall back to the first user regardless of role
                        first_admin = connection.execute(
                            "SELECT id FROM users ORDER BY created_at ASC LIMIT 1"
                        ).fetchone()
                    if first_admin:
                        connection.execute(
                            "INSERT INTO user_settings_new (user_id, key, value_json, updated_at) "
                            "SELECT ?, key, value_json, updated_at FROM user_settings",
                            (first_admin["id"],),
                        )
                connection.execute("DROP TABLE user_settings")
                connection.execute("ALTER TABLE user_settings_new RENAME TO user_settings")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_snapshots (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    source_session_id TEXT NOT NULL DEFAULT '',
                    item_count INTEGER NOT NULL DEFAULT 0,
                    items_json TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_snapshots_created_at ON sync_snapshots(created_at DESC)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS link_checks (
                    bookmark_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL DEFAULT '',
                    ok INTEGER NOT NULL DEFAULT 0,
                    status_code INTEGER NOT NULL DEFAULT 0,
                    error TEXT NOT NULL DEFAULT '',
                    checked_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS bookmarks_fts USING fts5(
                    bookmark_id UNINDEXED,
                    title,
                    url,
                    description,
                    domain,
                    tags,
                    collections,
                    notes
                )
                """
            )
            self.sync_search_index(connection)

    def list(self, query: str = "", filters: BookmarkFilters | None = None) -> list[Bookmark]:
        filters = filters or BookmarkFilters()
        if query.strip():
            return self.search(query, filters=filters)

        filter_sql, values = bookmark_filter_sql(filters)
        status_clause, status_values = bookmark_status_sql(filters.status)
        filter_sql.insert(0, status_clause)
        values = [*status_values, *values]
        where = f"WHERE {' AND '.join(filter_sql)}"
        order = bookmark_order_sql(filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM bookmarks b
                {where}
                ORDER BY {order}
                """,
                values,
            ).fetchall()
        return [bookmark_from_row(row) for row in rows]

    def search(self, query: str, filters: BookmarkFilters | None = None) -> list[Bookmark]:
        filters = filters or BookmarkFilters()
        if filters.status.strip().lower() != "active":
            return self.simple_search(query, filters=filters)

        fts_query = build_fts_query(query)
        if not fts_query:
            return self.list(filters=filters)

        filter_sql, filter_values = bookmark_filter_sql(filters)
        status_clause, status_values = bookmark_status_sql(filters.status)
        clauses = ["bookmarks_fts MATCH ?", status_clause, *filter_sql]
        values: list[Any] = [fts_query, *status_values, *filter_values]
        order = bookmark_order_sql(filters, prefix="b.")
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT b.*, bm25(bookmarks_fts) AS search_rank
                FROM bookmarks_fts
                JOIN bookmarks b ON b.id = bookmarks_fts.bookmark_id
                WHERE {' AND '.join(clauses)}
                ORDER BY search_rank ASC, {order}
                """,
                values,
            ).fetchall()
        return [bookmark_from_row(row) for row in rows]

    def simple_search(self, query: str, filters: BookmarkFilters) -> list[Bookmark]:
        terms = [term.strip().lower() for term in query.split() if term.strip()]
        filter_sql, values = bookmark_filter_sql(filters)
        status_clause, status_values = bookmark_status_sql(filters.status)
        clauses = [status_clause, *filter_sql]
        values = [*status_values, *values]
        for term in terms:
            clauses.append(
                """
                (
                    LOWER(b.title) LIKE ?
                    OR LOWER(b.url) LIKE ?
                    OR LOWER(b.description) LIKE ?
                    OR LOWER(b.domain) LIKE ?
                    OR LOWER(b.tags) LIKE ?
                    OR LOWER(b.collections) LIKE ?
                    OR LOWER(b.notes) LIKE ?
                )
                """
            )
            values.extend([f"%{term}%"] * 7)

        order = bookmark_order_sql(filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM bookmarks b
                WHERE {' AND '.join(clauses)}
                ORDER BY {order}
                """,
                values,
            ).fetchall()
        return [bookmark_from_row(row) for row in rows]

    def get(self, bookmark_id: str) -> Bookmark | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)).fetchone()
        return bookmark_from_row(row) if row else None

    def list_tags(self) -> list[dict[str, Any]]:
        """Return all tags used in active bookmarks, sorted by count descending."""
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT tags FROM bookmarks WHERE status = 'active' AND TRIM(tags) != ''"
            ).fetchall()
        counts: dict[str, int] = {}
        for row in rows:
            for tag in decode_list(row["tags"]):
                if tag:
                    counts[tag] = counts.get(tag, 0) + 1
        return sorted(
            [{"tag": t, "count": c} for t, c in counts.items()],
            key=lambda x: (-x["count"], x["tag"].lower()),
        )

    def list_collections(self) -> list[dict[str, Any]]:
        """Return all collections used in active bookmarks, sorted by count descending."""
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT collections FROM bookmarks WHERE status = 'active' AND TRIM(collections) != ''"
            ).fetchall()
        counts: dict[str, int] = {}
        for row in rows:
            for coll in decode_list(row["collections"]):
                if coll:
                    counts[coll] = counts.get(coll, 0) + 1
        return sorted(
            [{"collection": c, "count": n} for c, n in counts.items()],
            key=lambda x: (-x["count"], x["collection"].lower()),
        )

    def rename_tag(self, old_name: str, new_name: str) -> int:
        """Rename a tag across all active bookmarks. Returns count of updated bookmarks."""
        old_name = old_name.strip()
        new_name = new_name.strip()
        if not old_name or not new_name or old_name == new_name:
            return 0
        now = datetime.now(UTC).isoformat()
        updated = 0
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, tags FROM bookmarks WHERE status = 'active' AND tags LIKE ?",
                (f"%{old_name}%",),
            ).fetchall()
            for row in rows:
                tags = decode_list(row["tags"])
                if old_name in tags:
                    new_tags = encode_list([new_name if t == old_name else t for t in tags])
                    connection.execute(
                        "UPDATE bookmarks SET tags = ?, updated_at = ? WHERE id = ?",
                        (new_tags, now, row["id"]),
                    )
                    updated += 1
        return updated

    def delete_tag(self, name: str) -> int:
        """Remove a tag from all active bookmarks. Returns count of updated bookmarks."""
        name = name.strip()
        if not name:
            return 0
        now = datetime.now(UTC).isoformat()
        updated = 0
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, tags FROM bookmarks WHERE status = 'active' AND tags LIKE ?",
                (f"%{name}%",),
            ).fetchall()
            for row in rows:
                tags = decode_list(row["tags"])
                if name in tags:
                    new_tags = encode_list([t for t in tags if t != name])
                    connection.execute(
                        "UPDATE bookmarks SET tags = ?, updated_at = ? WHERE id = ?",
                        (new_tags, now, row["id"]),
                    )
                    updated += 1
        return updated

    def rename_collection(self, old_name: str, new_name: str) -> int:
        """Rename a collection across all active bookmarks. Returns count of updated bookmarks."""
        old_name = old_name.strip()
        new_name = new_name.strip()
        if not old_name or not new_name or old_name == new_name:
            return 0
        now = datetime.now(UTC).isoformat()
        updated = 0
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, collections FROM bookmarks WHERE status = 'active' AND collections LIKE ?",
                (f"%{old_name}%",),
            ).fetchall()
            for row in rows:
                colls = decode_list(row["collections"])
                if old_name in colls:
                    new_colls = encode_list([new_name if c == old_name else c for c in colls])
                    connection.execute(
                        "UPDATE bookmarks SET collections = ?, updated_at = ? WHERE id = ?",
                        (new_colls, now, row["id"]),
                    )
                    updated += 1
        return updated

    def delete_collection(self, name: str) -> int:
        """Remove a collection from all active bookmarks. Returns count of updated bookmarks."""
        name = name.strip()
        if not name:
            return 0
        now = datetime.now(UTC).isoformat()
        updated = 0
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, collections FROM bookmarks WHERE status = 'active' AND collections LIKE ?",
                (f"%{name}%",),
            ).fetchall()
            for row in rows:
                colls = decode_list(row["collections"])
                if name in colls:
                    new_colls = encode_list([c for c in colls if c != name])
                    connection.execute(
                        "UPDATE bookmarks SET collections = ?, updated_at = ? WHERE id = ?",
                        (new_colls, now, row["id"]),
                    )
                    updated += 1
        return updated

    def add(self, payload: dict[str, Any], *, enrich_metadata: bool = True) -> Bookmark:
        now = datetime.now(UTC).isoformat()
        payload = self.with_metadata(payload, enrich_metadata=enrich_metadata)
        bookmark = bookmark_from_payload(payload, bookmark_id=uuid4().hex, created_at=now, updated_at=now)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO bookmarks (
                    id, url, normalized_url, title, description, domain, favicon_url, tags, collections,
                    favorite, pinned, notes, status, merged_into, merged_at, source_browser, source_root,
                    source_folder_path, source_position, source_bookmark_id, archive_status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                bookmark_to_record(bookmark),
            )
            upsert_search_index(connection, bookmark)
        return bookmark

    def duplicate_preflight(self, url: str, *, exclude_id: str = "") -> dict[str, Any]:
        normalized_url = normalize_url(url)
        exact_url = url.strip()
        matches: dict[str, dict[str, Any]] = {}

        def add_match(bookmark: Bookmark, match_type: str, score: int, reason: str) -> None:
            if bookmark.id == exclude_id:
                return
            existing = matches.get(bookmark.id)
            if existing and existing["score"] >= score:
                return
            matches[bookmark.id] = {
                "match_type": match_type,
                "score": score,
                "reason": reason,
                "bookmark": bookmark.to_dict(),
            }

        with self.connect() as connection:
            for row in connection.execute(
                "SELECT * FROM bookmarks WHERE url = ? AND status = 'active'",
                (exact_url,),
            ).fetchall():
                add_match(bookmark_from_row(row), "exact_url", 100, "Exact URL already exists")

            for row in connection.execute(
                "SELECT * FROM bookmarks WHERE normalized_url = ? AND status = 'active'",
                (normalized_url,),
            ).fetchall():
                add_match(bookmark_from_row(row), "normalized_url", 95, "Normalized URL already exists")

            domain = domain_for_url(normalized_url)
            if domain:
                rows = connection.execute(
                    "SELECT * FROM bookmarks WHERE domain = ? AND normalized_url != ? AND status = 'active'",
                    (domain, normalized_url),
                ).fetchall()
                for row in rows:
                    bookmark = bookmark_from_row(row)
                    score = similar_url_score(normalized_url, bookmark.normalized_url)
                    if score >= 82:
                        add_match(bookmark, "similar_url", score, "Similar URL on the same domain")

        ordered = sorted(
            matches.values(),
            key=lambda item: (item["score"], item["bookmark"]["updated_at"]),
            reverse=True,
        )
        return {
            "url": exact_url,
            "normalized_url": normalized_url,
            "has_matches": bool(ordered),
            "matches": ordered[:10],
        }

    def category_suggestions(self, payload: dict[str, Any]) -> dict[str, Any]:
        enriched = self.with_metadata(payload, enrich_metadata=False)
        return category_suggestions(enriched)

    def update(self, bookmark_id: str, payload: dict[str, Any], *, enrich_metadata: bool = True) -> Bookmark | None:
        existing = self.get(bookmark_id)
        if not existing:
            return None

        merged = existing.to_dict()
        merged.update({key: value for key, value in payload.items() if value is not None})
        merged = self.with_metadata(merged, enrich_metadata=enrich_metadata and "url" in payload)
        bookmark = bookmark_from_payload(
            merged,
            bookmark_id=bookmark_id,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC).isoformat(),
        )
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE bookmarks
                SET url = ?, normalized_url = ?, title = ?, description = ?, domain = ?, favicon_url = ?,
                    tags = ?, collections = ?, favorite = ?, pinned = ?, notes = ?,
                    status = ?, merged_into = ?, merged_at = ?, source_browser = ?, source_root = ?,
                    source_folder_path = ?, source_position = ?, source_bookmark_id = ?,
                    archive_status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    bookmark.url,
                    bookmark.normalized_url,
                    bookmark.title,
                    bookmark.description,
                    bookmark.domain,
                    bookmark.favicon_url,
                    encode_list(bookmark.tags),
                    encode_list(bookmark.collections),
                    int(bookmark.favorite),
                    int(bookmark.pinned),
                    bookmark.notes,
                    bookmark.status,
                    bookmark.merged_into,
                    bookmark.merged_at,
                    bookmark.source_browser,
                    bookmark.source_root,
                    bookmark.source_folder_path,
                    bookmark.source_position,
                    bookmark.source_bookmark_id,
                    bookmark.archive_status,
                    bookmark.updated_at,
                    bookmark.id,
                ),
            )
            upsert_search_index(connection, bookmark)
        return bookmark

    def bulk_update(self, payload: dict[str, Any]) -> dict[str, Any]:
        ids = clean_list(payload.get("ids", []))
        if not ids:
            raise ValueError("ids are required")

        if to_bool(payload.get("delete", False)):
            deleted = sum(1 for bookmark_id in ids if self.delete(bookmark_id))
            with self.connect() as connection:
                self.record_activity(
                    connection,
                    kind="bulk_delete",
                    object_type="bookmark",
                    object_id=",".join(ids),
                    summary=f"Bulk-Loeschen: {deleted} Bookmark(s) geloescht",
                    details={"ids": ids, "deleted": deleted, "not_found": len(ids) - deleted},
                )
            return {"updated": 0, "deleted": deleted, "not_found": len(ids) - deleted, "bookmarks": []}

        updated: list[Bookmark] = []
        not_found = 0
        add_tags = clean_list(payload.get("add_tags", []))
        remove_tags = clean_list(payload.get("remove_tags", []))
        add_collections = clean_list(payload.get("add_collections", []))
        remove_collections = clean_list(payload.get("remove_collections", []))
        replace_collections = "set_collections" in payload
        set_collections = clean_list(payload.get("set_collections", []))

        for bookmark_id in ids:
            bookmark = self.get(bookmark_id)
            if not bookmark:
                not_found += 1
                continue

            changes: dict[str, Any] = {}
            if add_tags or remove_tags:
                changes["tags"] = remove_items(add_items(bookmark.tags, add_tags), remove_tags)
            if replace_collections:
                changes["collections"] = set_collections
            elif add_collections or remove_collections:
                changes["collections"] = remove_items(add_items(bookmark.collections, add_collections), remove_collections)
            if "favorite" in payload:
                changes["favorite"] = to_bool(payload["favorite"])
            if "pinned" in payload:
                changes["pinned"] = to_bool(payload["pinned"])

            if not changes:
                updated.append(bookmark)
                continue

            changed = self.update(bookmark_id, changes, enrich_metadata=False)
            if changed:
                updated.append(changed)

        with self.connect() as connection:
            self.record_activity(
                connection,
                kind="bulk_update",
                object_type="bookmark",
                object_id=",".join(ids),
                summary=f"Bulk-Update: {len(updated)} Bookmark(s) aktualisiert",
                details={
                    "ids": ids,
                    "updated": len(updated),
                    "not_found": not_found,
                    "add_tags": add_tags,
                    "remove_tags": remove_tags,
                    "add_collections": add_collections,
                    "remove_collections": remove_collections,
                    "set_collections": set_collections if replace_collections else [],
                    "favorite": payload.get("favorite"),
                    "pinned": payload.get("pinned"),
                },
            )
        return {
            "updated": len(updated),
            "deleted": 0,
            "not_found": not_found,
            "bookmarks": [bookmark.to_dict() for bookmark in updated],
        }

    def merge_duplicates(self, payload: dict[str, Any]) -> dict[str, Any]:
        winner_id = str(payload.get("winner_id", "")).strip()
        loser_ids = clean_list(payload.get("loser_ids", []))
        if not winner_id:
            raise ValueError("winner_id is required")
        if not loser_ids:
            raise ValueError("loser_ids are required")

        winner = self.get(winner_id)
        if not winner or winner.status != "active":
            raise ValueError("winner not found")

        losers = [bookmark for bookmark_id in loser_ids if (bookmark := self.get(bookmark_id))]
        losers = [bookmark for bookmark in losers if bookmark.id != winner_id and bookmark.status == "active"]
        if not losers:
            raise ValueError("no active losers found")

        merged_notes = merge_notes(winner, losers)
        now = datetime.now(UTC).isoformat()
        updated_winner_payload = {
            "tags": sorted({tag for bookmark in [winner, *losers] for tag in bookmark.tags}),
            "collections": sorted({collection for bookmark in [winner, *losers] for collection in bookmark.collections}),
            "favorite": winner.favorite or any(bookmark.favorite for bookmark in losers),
            "pinned": winner.pinned or any(bookmark.pinned for bookmark in losers),
            "notes": merged_notes,
        }
        winner_before = winner.to_dict()
        losers_before = [loser.to_dict() for loser in losers]
        updated_winner = self.update(winner_id, updated_winner_payload, enrich_metadata=False)
        if not updated_winner:
            raise ValueError("winner not found")

        merge_event_id = uuid4().hex
        with self.connect() as connection:
            for loser in losers:
                connection.execute(
                    """
                    UPDATE bookmarks
                    SET status = 'merged_duplicate', merged_into = ?, merged_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (winner_id, now, now, loser.id),
                )
                connection.execute("DELETE FROM bookmarks_fts WHERE bookmark_id = ?", (loser.id,))
            connection.execute(
                """
                INSERT INTO merge_events (
                    id, action, winner_id, loser_ids, winner_before_json,
                    losers_before_json, winner_after_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    merge_event_id,
                    "merge_duplicates",
                    winner_id,
                    json.dumps([loser.id for loser in losers], sort_keys=True),
                    json.dumps(winner_before, sort_keys=True),
                    json.dumps(losers_before, sort_keys=True),
                    json.dumps(updated_winner.to_dict(), sort_keys=True),
                    now,
                ),
            )
            self.record_activity(
                connection,
                kind="merge_duplicates",
                object_type="bookmark",
                object_id=winner_id,
                summary=f"Merge: {len(losers)} Dublette(n) in Gewinner uebernommen",
                details={
                    "winner_id": winner_id,
                    "loser_ids": [loser.id for loser in losers],
                    "merge_event_id": merge_event_id,
                },
            )
            self.create_conflict(
                connection,
                kind="merge_conflict",
                source_type="merge_event",
                source_id=merge_event_id,
                state="resolved",
                summary=f"Merge geprueft: {len(losers)} Dublette(n) in Gewinner uebernommen",
                details={
                    "winner_id": winner_id,
                    "loser_ids": [loser.id for loser in losers],
                    "winner_after": updated_winner.to_dict(),
                    "losers_before": losers_before,
                },
                timestamp=now,
            )

        merged_losers = [bookmark for loser in losers if (bookmark := self.get(loser.id))]

        return {
            "merge_event_id": merge_event_id,
            "winner": updated_winner.to_dict(),
            "merged_losers": [bookmark.to_dict() for bookmark in merged_losers],
            "merged_count": len(merged_losers),
            "deleted": 0,
        }

    def merge_history(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM merge_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [merge_event_from_row(row) for row in rows]

    def undo_merge(self, merge_event_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM merge_events WHERE id = ?", (merge_event_id,)).fetchone()
            if not row:
                raise ValueError("merge event not found")
            if row["action"] != "merge_duplicates":
                raise ValueError("merge event cannot be undone")
            if row["undone_at"]:
                raise ValueError("merge event already undone")

            winner_before = bookmark_from_snapshot(json.loads(row["winner_before_json"]))
            losers_before = [bookmark_from_snapshot(snapshot) for snapshot in json.loads(row["losers_before_json"])]
            winner_after = bookmark_from_snapshot(json.loads(row["winner_after_json"]))
            loser_ids = json.loads(row["loser_ids"])
            now = datetime.now(UTC).isoformat()

            save_bookmark(connection, winner_before)
            for loser in losers_before:
                save_bookmark(connection, loser)

            connection.execute("UPDATE merge_events SET undone_at = ? WHERE id = ?", (now, merge_event_id))
            self.record_activity(
                connection,
                kind="merge_undo",
                object_type="merge_event",
                object_id=merge_event_id,
                summary=f"Merge rueckgaengig gemacht: {len(loser_ids)} Bookmark(s) wiederhergestellt",
                details={
                    "merge_event_id": merge_event_id,
                    "winner_id": winner_before.id,
                    "loser_ids": loser_ids,
                    "winner_after_merge": winner_after.to_dict(),
                },
            )
            connection.execute(
                """
                UPDATE conflicts
                SET state = 'open', updated_at = ?, resolved_at = ''
                WHERE source_type = 'merge_event' AND source_id = ?
                """,
                (now, merge_event_id),
            )

        return {
            "merge_event_id": merge_event_id,
            "winner": winner_before.to_dict(),
            "restored_losers": [loser.to_dict() for loser in losers_before],
            "restored_count": len(losers_before),
            "undone_at": now,
        }

    def import_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM import_sessions
                ORDER BY imported_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [import_session_from_row(row) for row in rows]

    def restore_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM restore_sessions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        sessions = [restore_session_from_row(row) for row in rows]
        for session in sessions:
            session["conflict_groups"] = self.restore_session_conflict_groups(session["id"])
        return sessions

    def restore_session_conflict_groups(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM conflicts
                WHERE source_type = 'restore_session'
                AND json_extract(details_json, '$.restore_session_id') = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        restore_conflicts = [conflict_from_row(row) for row in rows]
        return summarize_restore_conflict_groups(restore_conflicts)

    def get_restore_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM restore_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        session = restore_session_from_row(row)
        session["conflict_groups"] = self.restore_session_conflict_groups(session_id)
        return session

    def apply_session_defaults(self, session_id: str) -> dict[str, Any]:
        """Resolve all open conflicts in a session by applying each conflict's suggested_action."""
        session = self.get_restore_session(session_id)
        if not session:
            raise ValueError("restore session not found")
        now = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM conflicts
                WHERE source_type = 'restore_session'
                AND json_extract(details_json, '$.restore_session_id') = ?
                AND state = 'open'
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
            resolved_count = 0
            skipped_count = 0
            for row in rows:
                details = json.loads(row["details_json"] or "{}")
                suggested = str(details.get("suggested_action", "")).strip()
                if not suggested:
                    skipped_count += 1
                    continue
                details["selected_action"] = suggested
                details["decision_explicit"] = False
                connection.execute(
                    """
                    UPDATE conflicts
                    SET state = 'resolved', details_json = ?, updated_at = ?, resolved_at = ?
                    WHERE id = ?
                    """,
                    (json.dumps(details, sort_keys=True), now, now, row["id"]),
                )
                resolved_count += 1
            self.record_activity(
                connection,
                kind="session_defaults_applied",
                object_type="restore_session",
                object_id=session_id,
                summary=f"Standardentscheidungen auf {resolved_count} offene Konflikte angewendet",
                details={
                    "restore_session_id": session_id,
                    "resolved_count": resolved_count,
                    "skipped_count": skipped_count,
                },
            )
        session = self.get_restore_session(session_id)
        return {
            "session_id": session_id,
            "resolved_count": resolved_count,
            "skipped_count": skipped_count,
            "session": session,
        }

    # ------------------------------------------------------------------
    # Sync baseline and drift detection
    # ------------------------------------------------------------------

    def record_sync_snapshot(
        self,
        items: list[dict[str, Any]],
        *,
        source_session_id: str = "",
    ) -> dict[str, Any]:
        """Save the current browser bookmark state as a sync baseline."""
        now = datetime.now(UTC).isoformat()
        snapshot_id = uuid4().hex
        clean_items = [
            {
                "url": str(item.get("url", "")),
                "title": str(item.get("title", "")),
                "folder_path": str(item.get("folder_path", "")),
                "id": str(item.get("id", "")),
            }
            for item in items
            if str(item.get("url", "")).strip()
        ]
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO sync_snapshots (id, created_at, source_session_id, item_count, items_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (snapshot_id, now, source_session_id, len(clean_items), json.dumps(clean_items, sort_keys=True)),
            )
            self.record_activity(
                connection,
                kind="sync_snapshot_recorded",
                object_type="sync_snapshot",
                object_id=snapshot_id,
                summary=f"Browser-Snapshot mit {len(clean_items)} Links gespeichert",
                details={"snapshot_id": snapshot_id, "item_count": len(clean_items), "source_session_id": source_session_id},
            )
        return {"id": snapshot_id, "created_at": now, "item_count": len(clean_items)}

    def get_latest_sync_snapshot(self) -> dict[str, Any] | None:
        """Return metadata for the most recent sync snapshot (no items_json to keep it light)."""
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, created_at, source_session_id, item_count FROM sync_snapshots ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "source_session_id": row["source_session_id"],
            "item_count": row["item_count"],
        }

    def compute_sync_drift(self, current_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Compare current browser state against last snapshot and active LinkVault bookmarks.

        Returns a structured report with four drift categories:
        - deleted_from_browser: in snapshot, not in current browser items
        - added_to_browser:     in current browser, not in snapshot
        - diverged:             URL in both but title or folder_path changed
        - linkvault_only:       active in LinkVault, not in current browser at all
        """
        snapshot_meta = self.get_latest_sync_snapshot()
        if not snapshot_meta:
            raise ValueError("no sync snapshot found — record a snapshot first via POST /api/sync/snapshot")

        with self.connect() as connection:
            row = connection.execute(
                "SELECT items_json FROM sync_snapshots WHERE id = ?",
                (snapshot_meta["id"],),
            ).fetchone()
        snapshot_items: list[dict[str, Any]] = json.loads(row["items_json"] or "[]")

        def url_key(item: dict[str, Any]) -> str:
            return comparable_url(normalize_url(str(item.get("url", ""))))

        snapshot_index = {url_key(i): i for i in snapshot_items if i.get("url")}
        current_index = {url_key(i): i for i in current_items if i.get("url")}

        lv_bookmarks = self.list(filters=BookmarkFilters(status="active"))
        lv_index = {comparable_url(normalize_url(bm.url)): bm for bm in lv_bookmarks}

        deleted: list[dict[str, Any]] = []
        added: list[dict[str, Any]] = []
        diverged: list[dict[str, Any]] = []
        linkvault_only: list[dict[str, Any]] = []

        for key, snap in snapshot_index.items():
            if key not in current_index:
                deleted.append({
                    "url": snap["url"],
                    "title": snap["title"],
                    "folder_path": snap["folder_path"],
                    "in_linkvault": key in lv_index,
                    "linkvault_id": lv_index[key].id if key in lv_index else "",
                })
            else:
                curr = current_index[key]
                changes = []
                if str(curr.get("title", "")) != str(snap.get("title", "")):
                    changes.append({"field": "title", "snapshot_value": snap.get("title"), "current_value": curr.get("title")})
                if str(curr.get("folder_path", "")) != str(snap.get("folder_path", "")):
                    changes.append({"field": "folder_path", "snapshot_value": snap.get("folder_path"), "current_value": curr.get("folder_path")})
                if changes:
                    diverged.append({
                        "url": snap["url"],
                        "title": curr.get("title") or snap["title"],
                        "changes": changes,
                        "in_linkvault": key in lv_index,
                        "linkvault_id": lv_index[key].id if key in lv_index else "",
                    })

        for key, curr in current_index.items():
            if key not in snapshot_index:
                added.append({
                    "url": curr["url"],
                    "title": curr["title"],
                    "folder_path": curr["folder_path"],
                    "in_linkvault": key in lv_index,
                })

        for key, bm in lv_index.items():
            if key not in current_index:
                linkvault_only.append({
                    "id": bm.id,
                    "url": bm.url,
                    "title": bm.title,
                })

        max_items = 100
        return {
            "snapshot_id": snapshot_meta["id"],
            "snapshot_at": snapshot_meta["created_at"],
            "snapshot_item_count": snapshot_meta["item_count"],
            "current_item_count": len(current_items),
            "has_drift": bool(deleted or added or diverged),
            "deleted_from_browser": {"count": len(deleted), "items": deleted[:max_items]},
            "added_to_browser": {"count": len(added), "items": added[:max_items]},
            "diverged": {"count": len(diverged), "items": diverged[:max_items]},
            "linkvault_only": {"count": len(linkvault_only), "items": linkvault_only[:max_items]},
        }

    # ------------------------------------------------------------------
    # Link health checks (light — favorites only)
    # ------------------------------------------------------------------

    def check_favorite_links(self) -> list[dict[str, Any]]:
        """Check HTTP reachability for all active favorites.

        Uses a thread pool (max 8) to parallelise HEAD/GET checks.
        Stores results in link_checks and returns the full list.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, url FROM bookmarks WHERE status = 'active' AND favorite = 1 ORDER BY created_at DESC"
            ).fetchall()

        items = [(row["id"], row["url"]) for row in rows]
        if not items:
            return []

        now = datetime.now(UTC).isoformat()
        raw_results: list[tuple[str, str, dict[str, Any]]] = []

        def _check(bookmark_id: str, url: str) -> tuple[str, str, dict[str, Any]]:
            return bookmark_id, url, check_url_health(url)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(_check, bid, url): bid for bid, url in items}
            for future in as_completed(futures):
                try:
                    raw_results.append(future.result())
                except Exception as exc:  # noqa: BLE001
                    bid = futures[future]
                    url = next(u for i, u in items if i == bid)
                    raw_results.append((bid, url, {"ok": False, "status_code": 0, "error": str(exc)}))

        with self.connect() as connection:
            for bookmark_id, url, result in raw_results:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO link_checks
                        (bookmark_id, url, ok, status_code, error, checked_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bookmark_id,
                        url,
                        int(bool(result.get("ok"))),
                        int(result.get("status_code", 0)),
                        str(result.get("error", "")),
                        now,
                    ),
                )

        self.record_activity("link_check_completed", {"favorite_count": len(raw_results), "checked_at": now})

        return [
            {
                "bookmark_id": bid,
                "url": url,
                "ok": bool(r.get("ok")),
                "status_code": int(r.get("status_code", 0)),
                "error": str(r.get("error", "")),
                "checked_at": now,
            }
            for bid, url, r in raw_results
        ]

    def favorites_report(self) -> dict[str, Any]:
        """Return a structured report of favorites needing attention.

        Categories:
        - uncategorized: favorites with no real collection (only Inbox or empty)
        - duplicated:    groups of favorites sharing the same normalized URL
        - dead:          favorites whose last link check returned not-ok
        """
        with self.connect() as connection:
            bm_rows = connection.execute(
                "SELECT * FROM bookmarks WHERE status = 'active' AND favorite = 1 ORDER BY created_at DESC"
            ).fetchall()
            check_rows = connection.execute(
                "SELECT bookmark_id, ok, status_code, error, checked_at FROM link_checks"
            ).fetchall()

        favorites = [bookmark_from_row(row) for row in bm_rows]
        checks = {row["bookmark_id"]: dict(row) for row in check_rows}

        # Uncategorized: only Inbox or no real collection
        uncategorized = []
        for bm in favorites:
            real = [c for c in bm.collections if c.strip() and c.strip().lower() != "inbox"]
            if not real:
                uncategorized.append(bm.to_dict())

        # Duplicated: same normalized_url among favorites
        url_groups: dict[str, list[dict[str, Any]]] = {}
        for bm in favorites:
            url_groups.setdefault(bm.normalized_url, []).append(bm.to_dict())
        duplicated = [
            {"normalized_url": url, "bookmarks": blist}
            for url, blist in url_groups.items()
            if len(blist) > 1
        ]

        # Dead: favorites with a not-ok check result
        fav_ids = {bm.id for bm in favorites}
        dead = []
        for bm in favorites:
            chk = checks.get(bm.id)
            if chk and not chk["ok"]:
                dead.append(
                    {
                        "bookmark": bm.to_dict(),
                        "check": {
                            "ok": bool(chk["ok"]),
                            "status_code": chk["status_code"],
                            "error": chk["error"],
                            "checked_at": chk["checked_at"],
                        },
                    }
                )

        checked_favs = {bid: c for bid, c in checks.items() if bid in fav_ids}
        ok_count = sum(1 for c in checked_favs.values() if c["ok"])
        last_checked_at = max((c["checked_at"] for c in checked_favs.values()), default="")

        return {
            "uncategorized": uncategorized,
            "duplicated": duplicated,
            "dead": dead,
            "check_summary": {
                "total_favorites": len(favorites),
                "total_checked": len(checked_favs),
                "ok": ok_count,
                "dead": len(checked_favs) - ok_count,
                "last_checked_at": last_checked_at,
            },
        }

    def collection_care_scores(self) -> list[dict[str, Any]]:
        """Return a care score (0-100) for each non-Inbox collection.

        Score factors (weights):
        - metadata  40 %: fraction of bookmarks with non-empty title AND description
        - dedup     30 %: fraction NOT sharing normalized_url with another bookmark
        - tags      15 %: fraction with at least one tag
        - links     15 %: fraction with ok link check (unchecked = neutral = 1.0)

        Lower scores surface collections that need the most attention.
        Sorted by score ascending (worst first).
        """
        with self.connect() as connection:
            bm_rows = connection.execute(
                "SELECT id, title, description, tags, collections, normalized_url FROM bookmarks WHERE status = 'active'"
            ).fetchall()
            dup_rows = connection.execute(
                """
                SELECT normalized_url FROM bookmarks
                WHERE status = 'active'
                GROUP BY normalized_url HAVING COUNT(*) > 1
                """
            ).fetchall()
            chk_rows = connection.execute(
                "SELECT bookmark_id, ok FROM link_checks"
            ).fetchall()

        dup_urls = {row["normalized_url"] for row in dup_rows}
        link_ok: dict[str, bool] = {row["bookmark_id"]: bool(row["ok"]) for row in chk_rows}

        # Group rows by collection (skip Inbox)
        coll_bmarks: dict[str, list[Any]] = {}
        for row in bm_rows:
            for coll in decode_list(str(row["collections"])):
                if not coll.strip() or coll.strip().lower() == "inbox":
                    continue
                coll_bmarks.setdefault(coll, []).append(row)

        result = []
        for coll, bmarks in coll_bmarks.items():
            n = len(bmarks)
            if n == 0:
                continue

            meta = sum(
                1 for b in bmarks if str(b["title"]).strip() and str(b["description"]).strip()
            ) / n

            dedup = sum(1 for b in bmarks if b["normalized_url"] not in dup_urls) / n

            tags = sum(1 for b in bmarks if decode_list(str(b["tags"]))) / n

            checked = [b for b in bmarks if b["id"] in link_ok]
            links = (sum(1 for b in checked if link_ok[b["id"]]) / len(checked)) if checked else 1.0

            score = int(round(meta * 40 + dedup * 30 + tags * 15 + links * 15))

            result.append(
                {
                    "collection": coll,
                    "count": n,
                    "score": score,
                    "factors": {
                        "metadata": int(round(meta * 100)),
                        "dedup": int(round(dedup * 100)),
                        "tags": int(round(tags * 100)),
                        "links": int(round(links * 100)),
                    },
                }
            )

        return sorted(result, key=lambda x: (x["score"], x["collection"]))

    def activity_events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM activity_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [activity_event_from_row(row) for row in rows]

    def conflicts(self, limit: int = 100, state: str = "all") -> list[dict[str, Any]]:
        query = [
            """
            SELECT *
            FROM conflicts
            """
        ]
        values: list[Any] = []
        normalized_state = normalize_conflict_state(state, allow_all=True)
        if normalized_state != "all":
            query.append("WHERE state = ?")
            values.append(normalized_state)
        query.append("ORDER BY created_at DESC LIMIT ?")
        values.append(limit)
        with self.connect() as connection:
            rows = connection.execute("\n".join(query), values).fetchall()
        return [conflict_from_row(row) for row in rows]

    def update_conflict_state(self, conflict_id: str, state: str) -> dict[str, Any]:
        normalized_state = normalize_conflict_state(state)
        now = datetime.now(UTC).isoformat()
        resolved_at = now if normalized_state == "resolved" else ""
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM conflicts WHERE id = ?", (conflict_id,)).fetchone()
            if not row:
                raise ValueError("conflict not found")
            connection.execute(
                """
                UPDATE conflicts
                SET state = ?, updated_at = ?, resolved_at = ?
                WHERE id = ?
                """,
                (normalized_state, now, resolved_at, conflict_id),
            )
            self.record_activity(
                connection,
                kind="conflict_state_changed",
                object_type="conflict",
                object_id=conflict_id,
                summary=f"Konflikt auf {normalized_state} gesetzt",
                details={
                    "conflict_id": conflict_id,
                    "kind": row["kind"],
                    "source_type": row["source_type"],
                    "source_id": row["source_id"],
                    "state": normalized_state,
                },
            )
            updated = connection.execute("SELECT * FROM conflicts WHERE id = ?", (conflict_id,)).fetchone()
        return conflict_from_row(updated)

    def update_conflict_decision(self, conflict_id: str, decision: str) -> dict[str, Any]:
        normalized_decision = normalize_preview_decision(decision)
        now = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM conflicts WHERE id = ?", (conflict_id,)).fetchone()
            if not row:
                raise ValueError("conflict not found")
            details = json.loads(row["details_json"] or "{}")
            details["selected_action"] = normalized_decision
            details["decision_explicit"] = True
            connection.execute(
                """
                UPDATE conflicts
                SET state = ?, details_json = ?, updated_at = ?, resolved_at = ?
                WHERE id = ?
                """,
                ("resolved", json.dumps(details, sort_keys=True), now, now, conflict_id),
            )
            self.record_activity(
                connection,
                kind="conflict_decision_changed",
                object_type="conflict",
                object_id=conflict_id,
                summary=f"Konfliktentscheidung auf {normalized_decision} gesetzt",
                details={
                    "conflict_id": conflict_id,
                    "kind": row["kind"],
                    "source_type": row["source_type"],
                    "source_id": row["source_id"],
                    "selected_action": normalized_decision,
                },
            )
            updated = connection.execute("SELECT * FROM conflicts WHERE id = ?", (conflict_id,)).fetchone()
        return conflict_from_row(updated)

    def apply_restore_conflict_group_decision(
        self,
        session_id: str,
        group_key: str,
        decision: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        normalized_group_key = str(group_key or "").strip()
        if not normalized_group_key:
            raise ValueError("group key required")
        normalized_decision = normalize_preview_decision(decision)
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM conflicts
                WHERE source_type = 'restore_session'
                ORDER BY created_at ASC
                """
            ).fetchall()
            matching_rows = []
            skipped_rows = 0
            for row in rows:
                conflict = conflict_from_row(row)
                details = conflict.get("details", {})
                if str(details.get("restore_session_id", "")) != session_id:
                    continue
                if str(conflict.get("group_key", "")) != normalized_group_key:
                    continue
                available_actions = details.get("available_actions", []) if isinstance(details.get("available_actions"), list) else []
                if available_actions and normalized_decision not in available_actions:
                    skipped_rows += 1
                    continue
                matching_rows.append((row, details))
            if not matching_rows:
                raise ValueError("restore conflict group not found")

            updated_count = 0
            for row, details in matching_rows:
                details["selected_action"] = normalized_decision
                details["decision_explicit"] = True
                connection.execute(
                    """
                    UPDATE conflicts
                    SET state = ?, details_json = ?, updated_at = ?, resolved_at = ?
                    WHERE id = ?
                    """,
                    ("resolved", json.dumps(details, sort_keys=True), now, now, row["id"]),
                )
                updated_count += 1

            self.record_activity(
                connection,
                kind="conflict_group_decision_changed",
                object_type="restore_session",
                object_id=session_id,
                summary=f"Konfliktgruppe {normalized_group_key} auf {normalized_decision} gesetzt",
                details={
                    "restore_session_id": session_id,
                    "group_key": normalized_group_key,
                    "selected_action": normalized_decision,
                    "updated_count": updated_count,
                    "skipped_count": skipped_rows,
                },
            )

            session_row = connection.execute(
                "SELECT * FROM restore_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if not session_row:
                raise ValueError("restore session not found")
        session = restore_session_from_row(session_row)
        session["conflict_groups"] = self.restore_session_conflict_groups(session_id)
        return {
            "session_id": session_id,
            "group_key": normalized_group_key,
            "selected_action": normalized_decision,
            "updated_count": updated_count,
            "skipped_count": skipped_rows,
            "session": session,
            "group": next((group for group in session["conflict_groups"] if group["group_key"] == normalized_group_key), None),
        }

    def preview_browser_restore(
        self,
        existing_items: list[dict[str, Any]],
        *,
        existing_folders: list[dict[str, Any]] | None = None,
        query: str = "",
        filters: BookmarkFilters | None = None,
        duplicate_action: str = "skip",
        target_mode: str = "new",
        target_folder_id: str = "",
        target_title: str = "",
        decisions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        filters = filters or BookmarkFilters(status="active")
        export_tree = self.browser_export_tree(query=query, filters=filters)
        records = flatten_browser_export_tree(export_tree)
        existing_index = browser_existing_index(existing_items)
        folder_index = browser_existing_folder_index(existing_folders or [])
        decision_map = {
            str(key): normalize_preview_decision(value) for key, value in (decisions or {}).items()
        }
        suggested_action = normalize_restore_action(duplicate_action)
        counts = {
            "create": 0,
            "skip_existing": 0,
            "update_existing": 0,
            "merge_existing": 0,
        }
        folder_counts = {
            "folder_create": 0,
            "reuse_existing_folder": 0,
            "folder_create_parallel": 0,
        }
        session_id = uuid4().hex
        preview_records: list[dict[str, Any]] = []
        folder_records: list[dict[str, Any]] = []
        conflict_total = 0
        decision_total = 0
        with self.connect() as connection:
            folder_plan = build_browser_restore_folder_plan(
                records,
                folder_index=folder_index,
                preview_id=session_id,
                target_mode=target_mode,
                target_folder_id=target_folder_id,
                target_title=target_title or export_tree["root_title"],
                decisions=decision_map,
            )
            for folder_record in folder_plan["folder_records"]:
                if folder_record["existing_folder"]:
                    explicit_decision = bool(folder_record["decision_explicit"])
                    if explicit_decision:
                        decision_total += 1
                    conflict_total += 1
                    conflict_id = self.create_conflict(
                        connection,
                        kind="browser_restore_structure_conflict",
                        source_type="restore_session",
                        source_id=folder_record["id"],
                        state="resolved" if explicit_decision else "open",
                        summary=f"Ordner-Konflikt beim Browser-Restore: {folder_record['title']}",
                        details={
                            "restore_session_id": session_id,
                            "folder_title": folder_record["title"],
                            "source_path": folder_record["source_path"],
                            "target_parent_path": folder_record["target_parent_path"],
                            "target_path": folder_record["target_path"],
                            "resolved_path": folder_record["resolved_path_text"],
                            "target_mode": target_mode,
                            "target_folder_id": target_folder_id,
                            "target_title": target_title,
                            "available_actions": folder_record["available_actions"],
                            "suggested_action": folder_record["suggested_action"],
                            "selected_action": folder_record["action"],
                            "decision_explicit": explicit_decision,
                            "existing_folder": folder_record["existing_folder"],
                            "action_preview": folder_record.get("action_preview", {}),
                        },
                    )
                    folder_record["conflict_id"] = conflict_id
                folder_counts[folder_record["action"]] += 1
                folder_records.append(folder_record)
            for record in records:
                resolved_path = folder_plan["resolved_paths"].get(tuple(record["path"]), record["path"])
                resolved_browser_path = [
                    *path_parts(folder_plan["target_root"]["path"]),
                    *resolved_path,
                ]
                existing = existing_index.get(comparable_url(normalize_url(str(record.get("url", "")))))
                action = "create"
                conflict_id = ""
                explicit_decision = False
                available_actions = ["create"]
                if existing:
                    available_actions = ["skip_existing", "merge_existing", "update_existing"]
                    action = suggested_action
                    if record["id"] in decision_map:
                        action = decision_map[record["id"]]
                        explicit_decision = True
                        decision_total += 1
                    conflict_total += 1
                    conflict_id = self.create_conflict(
                        connection,
                        kind="browser_restore_conflict",
                        source_type="restore_session",
                        source_id=record["id"],
                        state="resolved" if explicit_decision else "open",
                        summary=f"Browser-Restore-Konflikt: {record['title'] or record['url']}",
                        details={
                            "restore_session_id": session_id,
                            "url_raw": record["url"],
                            "url_normalized": comparable_url(normalize_url(record["url"])),
                            "target_path": " / ".join(record["path"]),
                            "resolved_path": " / ".join(resolved_browser_path),
                            "source_path": record["source_folder_path"],
                            "source_root": record["source_root"],
                            "target_mode": target_mode,
                            "target_folder_id": target_folder_id,
                            "target_title": target_title,
                            "available_actions": available_actions,
                            "suggested_action": suggested_action,
                            "selected_action": action,
                            "decision_explicit": explicit_decision,
                            "record": record,
                            "existing_bookmark": existing,
                            "action_preview": {
                                "skip_existing": {
                                    "effect": "keep_existing_link",
                                    "result_path": str(existing.get("folder_path", "")),
                                },
                                "merge_existing": {
                                    "effect": "merge_into_existing_link",
                                    "result_path": str(existing.get("folder_path", "")),
                                },
                                "update_existing": {
                                    "effect": "update_existing_link",
                                    "result_path": str(existing.get("folder_path", "")),
                                },
                            },
                        },
                    )
                counts[action] += 1
                preview_records.append(
                    {
                        **record,
                        "action": action,
                        "available_actions": available_actions,
                        "suggested_action": suggested_action if existing else "create",
                        "existing_bookmark": existing,
                        "decision_required": bool(existing and not explicit_decision),
                        "resolved_path": resolved_path,
                        "resolved_browser_path": resolved_browser_path,
                        "conflict_id": conflict_id,
                    }
                )
            connection.execute(
                """
                INSERT INTO restore_sessions (
                    id, source_name, target_mode, target_folder_id, target_title,
                    query, filters_json, duplicate_action, total_count, create_count,
                    skip_existing_count, merge_existing_count, update_existing_count,
                    conflict_count, structure_conflict_count, decision_count, state,
                    result_json, created_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    "browser_restore",
                    target_mode,
                    target_folder_id,
                    target_title,
                    query,
                    json.dumps(filters.to_dict(), sort_keys=True),
                    suggested_action,
                    len(records),
                    counts["create"],
                    counts["skip_existing"],
                    counts["merge_existing"],
                    counts["update_existing"],
                    conflict_total,
                    folder_plan["structure_conflict_count"],
                    decision_total,
                    "previewed",
                    json.dumps(
                        {
                            "target_root": folder_plan["target_root"],
                            "folder_counts": folder_counts,
                        },
                        sort_keys=True,
                    ),
                    datetime.now(UTC).isoformat(),
                    "",
                ),
            )
            self.record_activity(
                connection,
                kind="browser_restore_preview",
                object_type="restore_session",
                object_id=session_id,
                summary=f"Browser-Restore-Vorschau: {counts['create']} neu, {conflict_total} Konflikte",
                details={
                    "restore_session_id": session_id,
                    "query": query,
                    "filters": filters.to_dict(),
                    "target_mode": target_mode,
                    "target_folder_id": target_folder_id,
                    "target_title": target_title,
                    "duplicate_action": suggested_action,
                    "conflict_count": conflict_total,
                    "decision_count": decision_total,
                    "structure_conflict_count": folder_plan["structure_conflict_count"],
                    "target_root": folder_plan["target_root"],
                },
            )
        return {
            "session_id": session_id,
            "preview_id": session_id,
            "root_title": export_tree["root_title"],
            "total": len(records),
            "conflict_count": conflict_total,
            "decision_count": decision_total,
            "structure_conflict_count": folder_plan["structure_conflict_count"],
            "duplicate_action": suggested_action,
            "records": preview_records,
            "folder_records": folder_records,
            "target_root": folder_plan["target_root"],
            "tree": export_tree,
            **counts,
            **folder_counts,
        }

    def complete_restore_session(
        self,
        session_id: str,
        *,
        created: int,
        skipped_existing: int,
        merged_existing: int,
        updated_existing: int,
        root_title: str = "",
        status: str = "completed",
    ) -> dict[str, Any]:
        completed_at = datetime.now(UTC).isoformat()
        normalized_status = str(status or "completed").strip().lower()
        if normalized_status not in {"completed", "failed"}:
            normalized_status = "completed"
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM restore_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                raise ValueError("restore session not found")
            previous_result = json.loads(row["result_json"] or "{}")
            result = {
                **previous_result,
                "created": created,
                "skipped_existing": skipped_existing,
                "merged_existing": merged_existing,
                "updated_existing": updated_existing,
                "root_title": root_title,
            }
            connection.execute(
                """
                UPDATE restore_sessions
                SET state = ?, result_json = ?, completed_at = ?
                WHERE id = ?
                """,
                (normalized_status, json.dumps(result, sort_keys=True), completed_at, session_id),
            )
            self.record_activity(
                connection,
                kind="browser_restore_completed" if normalized_status == "completed" else "browser_restore_failed",
                object_type="restore_session",
                object_id=session_id,
                summary=(
                    f"Browser-Restore abgeschlossen: {created} erstellt, {skipped_existing} uebersprungen, "
                    f"{merged_existing} zusammengefuehrt, {updated_existing} aktualisiert"
                    if normalized_status == "completed"
                    else "Browser-Restore fehlgeschlagen"
                ),
                details={
                    "restore_session_id": session_id,
                    "created": created,
                    "skipped_existing": skipped_existing,
                    "merged_existing": merged_existing,
                    "updated_existing": updated_existing,
                    "root_title": root_title,
                    "state": normalized_status,
                },
            )
            updated = connection.execute(
                "SELECT * FROM restore_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return restore_session_from_row(updated)

    def get_setting(self, user_id: str, key: str, default: Any = None) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM user_settings WHERE user_id = ? AND key = ?", (user_id, key)
            ).fetchone()

        if not row:
            return {
                "key": key,
                "value": clone_json_value(default),
                "updated_at": "",
                "saved": False,
            }

        payload = stored_setting_from_row(row).to_dict()
        payload["saved"] = True
        return payload

    def set_setting(self, user_id: str, key: str, value: Any) -> dict[str, Any]:
        updated_at = datetime.now(UTC).isoformat()
        value_json = json.dumps(value, sort_keys=True)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO user_settings (user_id, key, value_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at
                """,
                (user_id, key, value_json, updated_at),
            )

        return {
            "key": key,
            "value": json.loads(value_json),
            "updated_at": updated_at,
            "saved": True,
        }

    def list_settings(self, user_id: str, prefix: str = "") -> list[dict[str, Any]]:
        if prefix:
            query = "SELECT * FROM user_settings WHERE user_id = ? AND key LIKE ? ORDER BY updated_at DESC, key ASC"
            parameters: tuple[Any, ...] = (user_id, f"{prefix}%")
        else:
            query = "SELECT * FROM user_settings WHERE user_id = ? ORDER BY updated_at DESC, key ASC"
            parameters = (user_id,)
        with self.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            {
                **stored_setting_from_row(row).to_dict(),
                "saved": True,
            }
            for row in rows
        ]

    def delete_setting(self, user_id: str, key: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM user_settings WHERE user_id = ? AND key = ?", (user_id, key)
            )
        return cursor.rowcount > 0

    def with_metadata(self, payload: dict[str, Any], *, enrich_metadata: bool) -> dict[str, Any]:
        if not enrich_metadata or not self.metadata_fetcher:
            return dict(payload)
        url = str(payload.get("url", "")).strip()
        if not url:
            return dict(payload)

        enriched = dict(payload)
        try:
            metadata = self.metadata_fetcher(url)
        except Exception:
            return enriched

        if metadata.final_url:
            enriched.setdefault("final_url", metadata.final_url)
        if metadata.title and not str(enriched.get("title", "")).strip():
            enriched["title"] = metadata.title
        if metadata.description and not str(enriched.get("description", "")).strip():
            enriched["description"] = metadata.description
        if metadata.favicon_url and not str(enriched.get("favicon_url", "")).strip():
            enriched["favicon_url"] = metadata.favicon_url
        return enriched

    def delete(self, bookmark_id: str) -> bool:
        with self.connect() as connection:
            bookmark = self.get(bookmark_id)
            connection.execute("DELETE FROM bookmarks_fts WHERE bookmark_id = ?", (bookmark_id,))
            cursor = connection.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
            if cursor.rowcount and bookmark:
                self.record_activity(
                    connection,
                    kind="bookmark_deleted",
                    object_type="bookmark",
                    object_id=bookmark_id,
                    summary=f"Bookmark geloescht: {bookmark.title or bookmark.url}",
                    details={"bookmark": bookmark.to_dict()},
                )
        return cursor.rowcount > 0

    ARCHIVE_STATUS_VALUES = {"", "pending", "archived", "failed"}

    def set_archive_status(self, bookmark_id: str, status: str) -> Bookmark | None:
        """Update only the archive_status field of a bookmark."""
        if status not in self.ARCHIVE_STATUS_VALUES:
            raise ValueError(f"Invalid archive_status: {status!r}. Must be one of: {sorted(self.ARCHIVE_STATUS_VALUES)}")
        bookmark = self.get(bookmark_id)
        if not bookmark:
            return None
        now = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            connection.execute(
                "UPDATE bookmarks SET archive_status = ?, updated_at = ? WHERE id = ?",
                (status, now, bookmark_id),
            )
        bookmark.archive_status = status
        bookmark.updated_at = now
        return bookmark

    def import_browser_html(self, html: str, *, session_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.import_items(parse_browser_html(html), session_meta=session_meta)

    def import_browser_bookmarks(self, items: list[dict[str, Any]], *, session_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.import_items(normalize_browser_bookmark_items(items), session_meta=session_meta)

    def import_chromium_json(self, data: str, *, session_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.import_items(parse_chromium_json(data), session_meta=session_meta)

    def import_firefox_json(self, data: str, *, session_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.import_items(parse_firefox_json(data), session_meta=session_meta)

    def import_safari_zip(self, data: str, *, session_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.import_items(parse_safari_zip(data), session_meta=session_meta)

    def import_linkding_json(self, data: str, *, session_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.import_items(parse_linkding_json(data), session_meta=session_meta)

    def preview_linkding_json_import(self, data: str) -> dict[str, Any]:
        return self.preview_import_items(parse_linkding_json(data))

    def import_firefox_jsonlz4(self, data: str, *, session_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.import_items(parse_firefox_jsonlz4(data), session_meta=session_meta)

    def import_generic(
        self,
        data: str,
        fmt: str,
        mapping: dict[str, str],
        *,
        session_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if fmt == "csv":
            items = parse_generic_csv(data, mapping)
        else:
            items = parse_generic_json(data, mapping)
        return self.import_items(items, session_meta=session_meta)

    def import_items(self, items: list[dict[str, Any]], *, session_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        created = 0
        duplicates = 0
        invalid = 0
        imported: list[Bookmark] = []
        session_records: list[dict[str, Any]] = []
        existing_urls = {bookmark.normalized_url for bookmark in self.list()}

        for item in items:
            raw_url = str(item.get("url", ""))
            try:
                normalized_url = normalize_url(raw_url)
            except ValueError:
                invalid += 1
                session_records.append(
                    {
                        "item_id": "",
                        "source_browser": str(item.get("source_browser", "")),
                        "source_path": str(item.get("source_folder_path", "")),
                        "source_id": str(item.get("source_bookmark_id", "")),
                        "url_raw": raw_url,
                        "url_normalized": "",
                        "action": "invalid_skipped",
                        "raw_payload_json": json.dumps(item, sort_keys=True),
                    }
                )
                continue
            if normalized_url in existing_urls:
                duplicates += 1
                session_records.append(
                    {
                        "item_id": "",
                        "source_browser": str(item.get("source_browser", "")),
                        "source_path": str(item.get("source_folder_path", "")),
                        "source_id": str(item.get("source_bookmark_id", "")),
                        "url_raw": raw_url,
                        "url_normalized": normalized_url,
                        "action": "duplicate_existing",
                        "raw_payload_json": json.dumps(item, sort_keys=True),
                    }
                )
                continue
            bookmark = self.add(item)
            existing_urls.add(bookmark.normalized_url)
            imported.append(bookmark)
            created += 1
            session_records.append(
                {
                    "item_id": bookmark.id,
                    "source_browser": bookmark.source_browser,
                    "source_path": bookmark.source_folder_path,
                    "source_id": bookmark.source_bookmark_id,
                    "url_raw": raw_url,
                    "url_normalized": bookmark.normalized_url,
                    "action": "created",
                    "raw_payload_json": json.dumps(item, sort_keys=True),
                }
            )

        session_id = ""
        if session_meta:
            summary = {
                "total_items": len(items),
                "created": created,
                "duplicates_skipped": duplicates,
                "invalid_skipped": invalid,
            }
            session_id = self.create_import_session(
                session_meta,
                summary=summary,
                created_count=created,
                duplicate_count=duplicates,
                conflict_count=duplicates,
                invalid_count=invalid,
                records=session_records,
            )

        return {
            "import_session_id": session_id,
            "created": created,
            "duplicates_skipped": duplicates,
            "invalid_skipped": invalid,
            "bookmarks": [bookmark.to_dict() for bookmark in imported],
        }

    def create_import_session(
        self,
        session_meta: dict[str, Any],
        *,
        summary: dict[str, Any],
        created_count: int,
        duplicate_count: int,
        conflict_count: int,
        invalid_count: int,
        records: list[dict[str, Any]],
    ) -> str:
        session_id = uuid4().hex
        imported_at = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO import_sessions (
                    id, source_name, source_format, source_file_name,
                    source_file_checksum_sha256, source_profile, sync_origin, imported_at,
                    created_count, duplicate_count, conflict_count, invalid_count, raw_summary_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    str(session_meta.get("source_name", "")),
                    str(session_meta.get("source_format", "")),
                    str(session_meta.get("source_file_name", "")),
                    str(session_meta.get("source_file_checksum_sha256", "")),
                    str(session_meta.get("source_profile", "")),
                    str(session_meta.get("sync_origin", "")),
                    imported_at,
                    created_count,
                    duplicate_count,
                    conflict_count,
                    invalid_count,
                    json.dumps(summary, sort_keys=True),
                ),
            )
            for record in records:
                connection.execute(
                    """
                    INSERT INTO import_records (
                        id, session_id, item_id, source_browser, source_path, source_id,
                        url_raw, url_normalized, action, raw_payload_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid4().hex,
                        session_id,
                        str(record.get("item_id", "")),
                        str(record.get("source_browser", "")),
                        str(record.get("source_path", "")),
                        str(record.get("source_id", "")),
                        str(record.get("url_raw", "")),
                        str(record.get("url_normalized", "")),
                        str(record.get("action", "")),
                        str(record.get("raw_payload_json", "{}")),
                        imported_at,
                    ),
                    )
            self.create_import_conflicts(connection, session_id, records, imported_at)
            self.record_activity(
                connection,
                kind="import_session_created",
                object_type="import_session",
                object_id=session_id,
                summary=f"Import {created_count} neu, {duplicate_count} Dubletten, {invalid_count} ungueltig",
                details={
                    "source_name": str(session_meta.get("source_name", "")),
                    "source_format": str(session_meta.get("source_format", "")),
                    "source_file_name": str(session_meta.get("source_file_name", "")),
                    "created_count": created_count,
                    "duplicate_count": duplicate_count,
                    "conflict_count": conflict_count,
                    "invalid_count": invalid_count,
                },
            )
        return session_id

    def create_import_conflicts(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        records: list[dict[str, Any]],
        created_at: str,
    ) -> None:
        for record in records:
            action = str(record.get("action", "")).strip()
            if action == "duplicate_existing":
                payload = json.loads(str(record.get("raw_payload_json", "{}")) or "{}")
                url = str(record.get("url_raw", "")).strip()
                self.create_conflict(
                    connection,
                    kind="import_duplicate",
                    source_type="import_session",
                    source_id=session_id,
                    state="open",
                    summary=f"Import-Dublette erkannt: {url or payload.get('title') or 'ohne URL'}",
                    details={
                        "session_id": session_id,
                        "action": action,
                        "url_raw": url,
                        "url_normalized": str(record.get("url_normalized", "")),
                        "source_browser": str(record.get("source_browser", "")),
                        "source_path": str(record.get("source_path", "")),
                        "source_id": str(record.get("source_id", "")),
                        "item": payload,
                    },
                    timestamp=created_at,
                )
            elif action == "invalid_skipped":
                payload = json.loads(str(record.get("raw_payload_json", "{}")) or "{}")
                url = str(record.get("url_raw", "")).strip()
                self.create_conflict(
                    connection,
                    kind="import_invalid",
                    source_type="import_session",
                    source_id=session_id,
                    state="open",
                    summary=f"Import uebersprungen: {url or payload.get('title') or 'ungueltiger Eintrag'}",
                    details={
                        "session_id": session_id,
                        "action": action,
                        "url_raw": url,
                        "source_browser": str(record.get("source_browser", "")),
                        "source_path": str(record.get("source_path", "")),
                        "source_id": str(record.get("source_id", "")),
                        "item": payload,
                    },
                    timestamp=created_at,
                )

    def create_conflict(
        self,
        connection: sqlite3.Connection,
        *,
        kind: str,
        source_type: str,
        source_id: str,
        state: str,
        summary: str,
        details: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> str:
        conflict_id = uuid4().hex
        created_at = timestamp or datetime.now(UTC).isoformat()
        normalized_state = normalize_conflict_state(state)
        resolved_at = created_at if normalized_state == "resolved" else ""
        connection.execute(
            """
            INSERT INTO conflicts (
                id, kind, source_type, source_id, state, summary,
                details_json, created_at, updated_at, resolved_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conflict_id,
                kind,
                source_type,
                source_id,
                normalized_state,
                summary,
                json.dumps(details or {}, sort_keys=True),
                created_at,
                created_at,
                resolved_at,
            ),
        )
        return conflict_id

    def record_activity(
        self,
        connection: sqlite3.Connection,
        *,
        kind: str,
        object_type: str,
        object_id: str,
        summary: str,
        details: dict[str, Any] | None = None,
    ) -> str:
        event_id = uuid4().hex
        connection.execute(
            """
            INSERT INTO activity_events (id, kind, object_type, object_id, summary, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                kind,
                object_type,
                object_id,
                summary,
                json.dumps(details or {}, sort_keys=True),
                datetime.now(UTC).isoformat(),
            ),
        )
        return event_id

    def preview_browser_html_import(self, html: str) -> dict[str, Any]:
        return self.preview_import_items(parse_browser_html(html))

    def preview_browser_bookmarks_import(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return self.preview_import_items(normalize_browser_bookmark_items(items))

    def preview_chromium_json_import(self, data: str) -> dict[str, Any]:
        return self.preview_import_items(parse_chromium_json(data))

    def preview_firefox_json_import(self, data: str) -> dict[str, Any]:
        return self.preview_import_items(parse_firefox_json(data))

    def preview_safari_zip_import(self, data: str) -> dict[str, Any]:
        return self.preview_import_items(parse_safari_zip(data))

    def preview_firefox_jsonlz4_import(self, data: str) -> dict[str, Any]:
        return self.preview_import_items(parse_firefox_jsonlz4(data))

    def preview_generic_import(self, data: str, fmt: str, mapping: dict[str, str]) -> dict[str, Any]:
        if fmt == "csv":
            items = parse_generic_csv(data, mapping)
        else:
            items = parse_generic_json(data, mapping)
        return self.preview_import_items(items)

    def infer_generic_import_columns(self, data: str, fmt: str) -> dict[str, Any]:
        """Detect column headers and return auto-inferred field mapping."""
        if fmt == "csv":
            reader = csv.DictReader(io.StringIO(data))
            headers = list(reader.fieldnames or [])
        else:
            try:
                payload = json.loads(data)
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid JSON.") from exc
            if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                headers = list(payload[0].keys())
            elif isinstance(payload, dict):
                for v in payload.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        headers = list(v[0].keys())
                        break
                else:
                    headers = list(payload.keys())
            else:
                headers = []
        return {"headers": headers, "inferred": infer_generic_columns(headers)}

    def preview_import_items(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        existing = {
            bookmark.normalized_url: bookmark
            for bookmark in self.list(filters=BookmarkFilters(status="all"))
        }
        seen_in_import: dict[str, int] = {}
        records: list[dict[str, Any]] = []
        counts = {
            "create": 0,
            "duplicate_existing": 0,
            "duplicate_in_import": 0,
            "invalid_skipped": 0,
        }

        for index, item in enumerate(items, start=1):
            raw_url = str(item.get("url", ""))
            try:
                normalized_url = normalize_url(raw_url)
            except ValueError as error:
                counts["invalid_skipped"] += 1
                records.append(
                    {
                        "index": index,
                        "url": raw_url,
                        "title": str(item.get("title") or raw_url),
                        "action": "invalid_skipped",
                        "error": str(error),
                    }
                )
                continue
            collections = clean_list(item.get("collections", [])) or ["Inbox"]
            tags = clean_list(item.get("tags", []))
            preview_item = {
                "index": index,
                "url": str(item.get("url", "")),
                "normalized_url": normalized_url,
                "domain": domain_for_url(normalized_url),
                "title": str(item.get("title") or item.get("url") or ""),
                "tags": tags,
                "collections": collections,
                "source_browser": str(item.get("source_browser", "")),
                "source_root": str(item.get("source_root", "")),
                "source_folder_path": str(item.get("source_folder_path", "")),
                "source_position": to_int(item.get("source_position", -1), -1),
                "source_bookmark_id": str(item.get("source_bookmark_id", "")),
                "suggestions": category_suggestions({**item, "tags": tags, "collections": collections}),
            }

            if normalized_url in existing:
                action = "duplicate_existing"
                preview_item["duplicate_bookmark"] = existing[normalized_url].to_dict()
            elif normalized_url in seen_in_import:
                action = "duplicate_in_import"
                preview_item["duplicate_of_index"] = seen_in_import[normalized_url]
            else:
                action = "create"

            preview_item["action"] = action
            counts[action] += 1
            records.append(preview_item)
            seen_in_import.setdefault(normalized_url, index)

        return {
            "total": len(items),
            **counts,
            "records": records,
        }

    def dedup_groups(self) -> list[dict[str, Any]]:
        groups: dict[str, list[Bookmark]] = {}
        for bookmark in self.list():
            groups.setdefault(bookmark.normalized_url, []).append(bookmark)

        result = []
        for normalized_url, bookmarks in groups.items():
            if len(bookmarks) < 2:
                continue
            winner = choose_winner(bookmarks)
            result.append(
                {
                    "normalized_url": normalized_url,
                    "winner_id": winner.id,
                    "score": 100,
                    "reason": "Exact normalized URL match",
                    "items": [bookmark.to_dict() for bookmark in bookmarks],
                }
            )
        return result

    def dedup_dry_run(self) -> dict[str, Any]:
        groups = []
        for group in self.dedup_groups():
            winner_id = group["winner_id"]
            losers = [item for item in group["items"] if item["id"] != winner_id]
            winner = next(item for item in group["items"] if item["id"] == winner_id)
            tags = sorted({tag for item in group["items"] for tag in item["tags"]})
            collections = sorted({collection for item in group["items"] for collection in item["collections"]})
            groups.append(
                {
                    **group,
                    "winner": winner,
                    "winner_reason": winner_reason_label(winner, group["items"]),
                    "differences": group_differences(group["items"], winner_id),
                    "merge_plan": {
                        "winner_id": winner_id,
                        "loser_ids": [item["id"] for item in losers],
                        "keep_title": winner["title"],
                        "keep_description": winner["description"],
                        "move_tags": tags,
                        "move_collections": collections,
                        "append_notes_from_losers": [item["notes"] for item in losers if item["notes"]],
                        "keep_favorite": any(item["favorite"] for item in group["items"]),
                        "keep_pinned": any(item["pinned"] for item in group["items"]),
                        "delete_losers": False,
                    },
                }
            )
        return {"groups": groups, "group_count": len(groups)}

    def browser_export_tree(self, query: str = "", filters: BookmarkFilters | None = None) -> dict[str, Any]:
        filters = filters or BookmarkFilters(status="active")
        bookmarks = self.list(query=query, filters=filters)
        roots: dict[str, dict[str, Any]] = {}

        for bookmark in sorted(bookmarks, key=browser_export_sort_key):
            root_title = bookmark.source_root.strip() or "LinkVault"
            folder_path = export_folder_path(bookmark)
            root = roots.setdefault(
                root_title,
                {
                    "title": root_title,
                    "source_root": bookmark.source_root.strip(),
                    "children": [],
                    "_folders": {},
                },
            )
            parent = root
            path_accumulator: list[str] = []
            for folder in folder_path:
                path_accumulator.append(folder)
                folder_key = "\n".join(path_accumulator)
                folder_node = root["_folders"].get(folder_key)
                if not folder_node:
                    folder_node = {
                        "type": "folder",
                        "title": folder,
                        "source_folder_path": " / ".join(path_accumulator),
                        "children": [],
                        "_folders": {},
                    }
                    root["_folders"][folder_key] = folder_node
                    parent["children"].append(folder_node)
                parent = folder_node

            parent["children"].append(
                {
                    "type": "bookmark",
                    "id": bookmark.id,
                    "title": bookmark.title or bookmark.url,
                    "url": bookmark.url,
                    "tags": bookmark.tags,
                    "collections": bookmark.collections,
                    "source_browser": bookmark.source_browser,
                    "source_root": bookmark.source_root,
                    "source_folder_path": bookmark.source_folder_path,
                    "source_position": bookmark.source_position,
                    "source_bookmark_id": bookmark.source_bookmark_id,
                }
            )

        clean_roots = [strip_internal_folder_maps(root) for root in roots.values()]
        return {
            "root_title": f"LinkVault Import {datetime.now(UTC).date().isoformat()}",
            "bookmark_count": len(bookmarks),
            "query": query,
            "filters": {
                "favorite": filters.favorite,
                "pinned": filters.pinned,
                "domain": filters.domain,
                "tag": filters.tag,
                "collection": filters.collection,
                "status": filters.status,
            },
            "roots": clean_roots,
        }

    def sync_search_index(self, connection: sqlite3.Connection) -> None:
        bookmark_count = connection.execute("SELECT COUNT(*) FROM bookmarks WHERE status = 'active'").fetchone()[0]
        fts_count = connection.execute("SELECT COUNT(*) FROM bookmarks_fts").fetchone()[0]
        stale_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM bookmarks_fts
            LEFT JOIN bookmarks b ON b.id = bookmarks_fts.bookmark_id
            WHERE b.id IS NULL OR b.status != 'active'
            """
        ).fetchone()[0]
        if bookmark_count != fts_count or stale_count:
            rebuild_search_index(connection)


def bookmark_from_payload(
    payload: dict[str, Any],
    *,
    bookmark_id: str,
    created_at: str,
    updated_at: str,
) -> Bookmark:
    url = str(payload.get("url", "")).strip()
    normalized_url = normalize_url(url)
    title = str(payload.get("title") or url).strip()
    collections = clean_list(payload.get("collections", [])) or ["Inbox"]
    return Bookmark(
        id=bookmark_id,
        url=url,
        normalized_url=normalized_url,
        title=title or url,
        description=str(payload.get("description", "")),
        domain=domain_for_url(normalized_url),
        favicon_url=str(payload.get("favicon_url", "")),
        tags=clean_list(payload.get("tags", [])),
        collections=collections,
        favorite=to_bool(payload.get("favorite", False)),
        pinned=to_bool(payload.get("pinned", False)),
        notes=str(payload.get("notes", "")),
        status=str(payload.get("status", "active")),
        merged_into=str(payload.get("merged_into", "")),
        merged_at=str(payload.get("merged_at", "")),
        source_browser=str(payload.get("source_browser", "")),
        source_root=str(payload.get("source_root", "")),
        source_folder_path=str(payload.get("source_folder_path", "")),
        source_position=to_int(payload.get("source_position", -1), -1),
        source_bookmark_id=str(payload.get("source_bookmark_id", "")),
        archive_status=str(payload.get("archive_status", "")),
        created_at=created_at,
        updated_at=updated_at,
    )


def bookmark_from_row(row: sqlite3.Row) -> Bookmark:
    return Bookmark(
        id=row["id"],
        url=row["url"],
        normalized_url=row["normalized_url"],
        title=row["title"],
        description=row["description"],
        domain=row["domain"],
        favicon_url=row["favicon_url"],
        tags=decode_list(row["tags"]),
        collections=decode_list(row["collections"]),
        favorite=bool(row["favorite"]),
        pinned=bool(row["pinned"]),
        notes=row["notes"],
        status=row["status"],
        merged_into=row["merged_into"],
        merged_at=row["merged_at"],
        source_browser=row["source_browser"],
        source_root=row["source_root"],
        source_folder_path=row["source_folder_path"],
        source_position=row["source_position"],
        source_bookmark_id=row["source_bookmark_id"],
        archive_status=row["archive_status"] if "archive_status" in row.keys() else "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def bookmark_from_snapshot(payload: dict[str, Any]) -> Bookmark:
    return Bookmark(
        id=str(payload["id"]),
        url=str(payload["url"]),
        normalized_url=str(payload.get("normalized_url") or normalize_url(str(payload["url"]))),
        title=str(payload.get("title", "")),
        description=str(payload.get("description", "")),
        domain=str(payload.get("domain", "")),
        favicon_url=str(payload.get("favicon_url", "")),
        tags=clean_list(payload.get("tags", [])),
        collections=clean_list(payload.get("collections", [])) or ["Inbox"],
        favorite=to_bool(payload.get("favorite", False)),
        pinned=to_bool(payload.get("pinned", False)),
        notes=str(payload.get("notes", "")),
        status=str(payload.get("status", "active")),
        merged_into=str(payload.get("merged_into", "")),
        merged_at=str(payload.get("merged_at", "")),
        source_browser=str(payload.get("source_browser", "")),
        source_root=str(payload.get("source_root", "")),
        source_folder_path=str(payload.get("source_folder_path", "")),
        source_position=to_int(payload.get("source_position", -1), -1),
        source_bookmark_id=str(payload.get("source_bookmark_id", "")),
        archive_status=str(payload.get("archive_status", "")),
        created_at=str(payload.get("created_at", datetime.now(UTC).isoformat())),
        updated_at=str(payload.get("updated_at", datetime.now(UTC).isoformat())),
    )


def bookmark_to_record(bookmark: Bookmark) -> tuple[Any, ...]:
    return (
        bookmark.id,
        bookmark.url,
        bookmark.normalized_url,
        bookmark.title,
        bookmark.description,
        bookmark.domain,
        bookmark.favicon_url,
        encode_list(bookmark.tags),
        encode_list(bookmark.collections),
        int(bookmark.favorite),
        int(bookmark.pinned),
        bookmark.notes,
        bookmark.status,
        bookmark.merged_into,
        bookmark.merged_at,
        bookmark.source_browser,
        bookmark.source_root,
        bookmark.source_folder_path,
        bookmark.source_position,
        bookmark.source_bookmark_id,
        bookmark.archive_status,
        bookmark.created_at,
        bookmark.updated_at,
    )


def save_bookmark(connection: sqlite3.Connection, bookmark: Bookmark) -> None:
    connection.execute(
        """
        INSERT INTO bookmarks (
            id, url, normalized_url, title, description, domain, favicon_url, tags, collections,
            favorite, pinned, notes, status, merged_into, merged_at, source_browser, source_root,
            source_folder_path, source_position, source_bookmark_id, archive_status, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            url = excluded.url,
            normalized_url = excluded.normalized_url,
            title = excluded.title,
            description = excluded.description,
            domain = excluded.domain,
            favicon_url = excluded.favicon_url,
            tags = excluded.tags,
            collections = excluded.collections,
            favorite = excluded.favorite,
            pinned = excluded.pinned,
            notes = excluded.notes,
            status = excluded.status,
            merged_into = excluded.merged_into,
            merged_at = excluded.merged_at,
            source_browser = excluded.source_browser,
            source_root = excluded.source_root,
            source_folder_path = excluded.source_folder_path,
            source_position = excluded.source_position,
            source_bookmark_id = excluded.source_bookmark_id,
            archive_status = excluded.archive_status,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at
        """,
        bookmark_to_record(bookmark),
    )
    upsert_search_index(connection, bookmark)


def merge_event_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "action": row["action"],
        "winner_id": row["winner_id"],
        "loser_ids": json.loads(row["loser_ids"]),
        "winner_before": json.loads(row["winner_before_json"]),
        "losers_before": json.loads(row["losers_before_json"]),
        "winner_after": json.loads(row["winner_after_json"]),
        "created_at": row["created_at"],
        "undone_at": row["undone_at"],
        "can_undo": not bool(row["undone_at"]),
    }


def import_session_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return ImportSession(
        id=row["id"],
        source_name=row["source_name"],
        source_format=row["source_format"],
        source_file_name=row["source_file_name"],
        source_file_checksum_sha256=row["source_file_checksum_sha256"],
        source_profile=row["source_profile"],
        sync_origin=row["sync_origin"],
        imported_at=row["imported_at"],
        created_count=row["created_count"],
        duplicate_count=row["duplicate_count"],
        conflict_count=row["conflict_count"],
        invalid_count=row["invalid_count"],
        raw_summary_json=row["raw_summary_json"],
    ).to_dict()


def restore_session_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return RestoreSession(
        id=row["id"],
        source_name=row["source_name"],
        target_mode=row["target_mode"],
        target_folder_id=row["target_folder_id"],
        target_title=row["target_title"],
        query=row["query"],
        filters_json=row["filters_json"],
        duplicate_action=row["duplicate_action"],
        total_count=row["total_count"],
        create_count=row["create_count"],
        skip_existing_count=row["skip_existing_count"],
        merge_existing_count=row["merge_existing_count"],
        update_existing_count=row["update_existing_count"],
        conflict_count=row["conflict_count"],
        structure_conflict_count=row["structure_conflict_count"],
        decision_count=row["decision_count"],
        state=row["state"],
        result_json=row["result_json"],
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    ).to_dict()


def activity_event_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return ActivityEvent(
        id=row["id"],
        kind=row["kind"],
        object_type=row["object_type"],
        object_id=row["object_id"],
        summary=row["summary"],
        details_json=row["details_json"],
        created_at=row["created_at"],
    ).to_dict()


def conflict_from_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = ConflictRecord(
        id=row["id"],
        kind=row["kind"],
        source_type=row["source_type"],
        source_id=row["source_id"],
        state=row["state"],
        summary=row["summary"],
        details_json=row["details_json"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        resolved_at=row["resolved_at"],
    ).to_dict()
    if payload["source_type"] == "restore_session":
        meta = restore_conflict_group_meta(payload)
        payload.update(meta)
    return payload


def stored_setting_from_row(row: sqlite3.Row) -> StoredSetting:
    return StoredSetting(
        key=row["key"],
        value_json=row["value_json"],
        updated_at=row["updated_at"],
    )


def clone_json_value(value: Any) -> Any:
    return json.loads(json.dumps(value))


def normalize_conflict_state(value: Any, *, allow_all: bool = False) -> str:
    state = str(value or "open").strip().lower()
    allowed = {"open", "resolved", "ignored"}
    if allow_all:
        allowed = {*allowed, "all"}
    if state not in allowed:
        return "all" if allow_all else "open"
    return state


def restore_conflict_group_meta(conflict: dict[str, Any]) -> dict[str, Any]:
    details = conflict.get("details", {}) if isinstance(conflict.get("details"), dict) else {}
    source_id = str(conflict.get("source_id", ""))
    if conflict.get("kind") == "browser_restore_structure_conflict":
        is_target_root = source_id.startswith("root::") or not str(details.get("target_parent_path", "")).strip()
        if is_target_root:
            return {
                "group_key": "target_root",
                "group_title": "Zielordner",
                "group_description": "Restore-Ziel kollidiert mit einem vorhandenen Browser-Ordner.",
            }
        return {
            "group_key": "structure",
            "group_title": "Bestehende Struktur",
            "group_description": "Ordnerpfade kollidieren mit der vorhandenen Browser-Struktur.",
        }
    if conflict.get("kind") == "browser_restore_conflict":
        return {
            "group_key": "existing_links",
            "group_title": "Vorhandene Links",
            "group_description": "Links existieren bereits im Ziel und brauchen eine Sync-/Restore-Entscheidung.",
        }
    return {
        "group_key": "other",
        "group_title": "Weitere Konflikte",
        "group_description": "Weitere Restore-Konflikte ohne feste Gruppe.",
    }


def summarize_restore_conflict_groups(conflicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for conflict in conflicts:
        session_id = str(conflict.get("details", {}).get("restore_session_id", ""))
        group_key = str(conflict.get("group_key", "other"))
        group_title = str(conflict.get("group_title", "Weitere Konflikte"))
        group_description = str(conflict.get("group_description", ""))
        entry = grouped.setdefault(
            (session_id, group_key),
            {
                "session_id": session_id,
                "group_key": group_key,
                "group_title": group_title,
                "group_description": group_description,
                "total_count": 0,
                "open_count": 0,
                "resolved_count": 0,
                "ignored_count": 0,
                "explicit_decision_count": 0,
                "available_actions": [],
                "selected_actions": {},
                "paths": [],
                "target_paths": [],
                "conflict_ids": [],
                "action_previews": {},
            },
        )
        entry["total_count"] += 1
        state = str(conflict.get("state", "open"))
        entry[f"{state}_count"] = entry.get(f"{state}_count", 0) + 1
        details = conflict.get("details", {}) if isinstance(conflict.get("details"), dict) else {}
        if details.get("decision_explicit"):
            entry["explicit_decision_count"] += 1
        selected_action = str(details.get("selected_action", "")).strip()
        if selected_action:
            entry["selected_actions"][selected_action] = entry["selected_actions"].get(selected_action, 0) + 1
        for action in details.get("available_actions", []) if isinstance(details.get("available_actions"), list) else []:
            if action not in entry["available_actions"]:
                entry["available_actions"].append(action)
        source_path = str(details.get("source_path", "")).strip()
        if source_path and source_path not in entry["paths"]:
            entry["paths"].append(source_path)
        target_path = str(details.get("resolved_path") or details.get("target_path") or "").strip()
        if target_path and target_path not in entry["target_paths"]:
            entry["target_paths"].append(target_path)
        entry["conflict_ids"].append(str(conflict.get("id", "")))
        action_preview_map = details.get("action_preview", {}) if isinstance(details.get("action_preview"), dict) else {}
        for action, preview in action_preview_map.items():
            if not isinstance(preview, dict):
                continue
            action_entry = entry["action_previews"].setdefault(
                action,
                {
                    "action": action,
                    "count": 0,
                    "effects": {},
                    "path_examples": [],
                },
            )
            action_entry["count"] += 1
            effect = str(preview.get("effect", "")).strip()
            if effect:
                action_entry["effects"][effect] = action_entry["effects"].get(effect, 0) + 1
            result_path = str(preview.get("result_path", "")).strip()
            if result_path and result_path not in action_entry["path_examples"] and len(action_entry["path_examples"]) < 3:
                action_entry["path_examples"].append(result_path)

    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        order = {"target_root": 0, "structure": 1, "existing_links": 2, "other": 3}
        return (order.get(item["group_key"], 99), item["group_title"])

    summarized = list(grouped.values())
    for entry in summarized:
        entry["paths"] = entry["paths"][:3]
        entry["target_paths"] = entry["target_paths"][:3]
    return sorted(summarized, key=sort_key)


def checksum_for_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def upsert_search_index(connection: sqlite3.Connection, bookmark: Bookmark) -> None:
    connection.execute("DELETE FROM bookmarks_fts WHERE bookmark_id = ?", (bookmark.id,))
    if bookmark.status != "active":
        return
    connection.execute(
        """
        INSERT INTO bookmarks_fts (bookmark_id, title, url, description, domain, tags, collections, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        search_record(bookmark),
    )


def rebuild_search_index(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM bookmarks_fts")
    rows = connection.execute("SELECT * FROM bookmarks WHERE status = 'active'").fetchall()
    for row in rows:
        upsert_search_index(connection, bookmark_from_row(row))


def search_record(bookmark: Bookmark) -> tuple[str, str, str, str, str, str, str, str]:
    return (
        bookmark.id,
        bookmark.title,
        bookmark.url,
        bookmark.description,
        bookmark.domain,
        encode_list(bookmark.tags),
        encode_list(bookmark.collections),
        bookmark.notes,
    )


def build_fts_query(query: str) -> str:
    terms = [term.strip() for term in query.split() if term.strip()]
    return " AND ".join(quote_fts_term(term) for term in terms)


def quote_fts_term(term: str) -> str:
    escaped = term.replace('"', '""')
    return f'"{escaped}"*'


def bookmark_order_sql(filters: BookmarkFilters, prefix: str = "") -> str:
    """Build ORDER BY clause from sort_by / sort_order in filters.

    The primary sort column comes first, followed by fixed tie-breakers so
    the result is always deterministic.  ``prefix`` is prepended to each
    column name (e.g. ``"b."`` for JOIN queries).
    """
    sort_by = filters.sort_by if filters.sort_by in BOOKMARK_SORT_FIELDS else "created_at"
    direction = "ASC" if filters.sort_order == "asc" else "DESC"
    p = prefix

    # Primary column with chosen direction
    primary = f"{p}{sort_by} {direction}"

    # Tie-breakers: always stable regardless of primary sort
    if sort_by == "title":
        # Secondary: domain, then newest first
        tiebreakers = f"{p}domain ASC, {p}created_at DESC"
    elif sort_by == "domain":
        # Secondary: title alphabetical, then newest first
        tiebreakers = f"{p}title ASC, {p}created_at DESC"
    else:
        # created_at or updated_at: title alphabetical as tie-breaker
        tiebreakers = f"{p}title ASC"

    return f"{primary}, {tiebreakers}"


def bookmark_filter_sql(filters: BookmarkFilters) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    if filters.favorite is not None:
        clauses.append("b.favorite = ?")
        values.append(int(filters.favorite))
    if filters.pinned is not None:
        clauses.append("b.pinned = ?")
        values.append(int(filters.pinned))
    if filters.domain.strip():
        clauses.append("LOWER(b.domain) = LOWER(?)")
        values.append(filters.domain.strip())
    if filters.tag.strip():
        clauses.append("('\n' || b.tags || '\n') LIKE ?")
        values.append(f"%\n{filters.tag.strip()}\n%")
    if filters.collection.strip():
        clauses.append("('\n' || b.collections || '\n') LIKE ?")
        values.append(f"%\n{filters.collection.strip()}\n%")
    return clauses, values


def bookmark_status_sql(status: str) -> tuple[str, list[Any]]:
    status = status.strip().lower()
    if status == "all":
        return "1 = 1", []
    if status in {"active", "merged_duplicate"}:
        return "b.status = ?", [status]
    return "b.status = ?", ["active"]


DOMAIN_CATEGORY_RULES: dict[str, tuple[list[str], list[str]]] = {
    "github.com": (["code", "github"], ["Development"]),
    "gitlab.com": (["code", "gitlab"], ["Development"]),
    "docs.python.org": (["python", "docs"], ["Development", "Documentation"]),
    "developer.mozilla.org": (["web", "docs"], ["Development", "Documentation"]),
    "stackoverflow.com": (["code", "qa"], ["Development"]),
    "community-scripts.org": (["proxmox", "selfhost"], ["Homelab/Proxmox"]),
    "reddit.com": (["community"], ["Reading"]),
    "news.ycombinator.com": (["tech", "news"], ["Reading"]),
    "youtube.com": (["video"], ["Watch Later"]),
}

KEYWORD_CATEGORY_RULES: dict[str, tuple[list[str], list[str]]] = {
    "proxmox": (["proxmox", "homelab"], ["Homelab/Proxmox"]),
    "lxc": (["proxmox", "container"], ["Homelab/Proxmox"]),
    "selfhost": (["selfhost"], ["Homelab"]),
    "docker": (["docker", "container"], ["Development"]),
    "python": (["python"], ["Development"]),
    "sqlite": (["sqlite", "database"], ["Development"]),
    "backup": (["backup"], ["Operations"]),
    "restore": (["backup"], ["Operations"]),
    "security": (["security"], ["Security"]),
    "auth": (["auth", "security"], ["Security"]),
    "api": (["api"], ["Development"]),
    "documentation": (["docs"], ["Documentation"]),
    "docs": (["docs"], ["Documentation"]),
    "tutorial": (["learning"], ["Reading"]),
    "guide": (["learning"], ["Reading"]),
}


def category_suggestions(payload: dict[str, Any]) -> dict[str, Any]:
    url = str(payload.get("url", "")).strip()
    normalized_url = normalize_url(url)
    domain = domain_for_url(normalized_url)
    text = " ".join(
        [
            normalized_url,
            str(payload.get("title", "")),
            str(payload.get("description", "")),
            str(payload.get("notes", "")),
        ]
    ).lower()
    existing_tags = set(clean_list(payload.get("tags", [])))
    existing_collections = set(clean_list(payload.get("collections", [])))
    suggested_tags: set[str] = set()
    suggested_collections: set[str] = set()
    reasons: list[str] = []

    domain_candidates = domain_candidates_for(domain)
    for candidate in domain_candidates:
        if candidate in DOMAIN_CATEGORY_RULES:
            tags, collections = DOMAIN_CATEGORY_RULES[candidate]
            suggested_tags.update(tags)
            suggested_collections.update(collections)
            reasons.append(f"Domain: {candidate}")
            break

    for keyword, (tags, collections) in KEYWORD_CATEGORY_RULES.items():
        if keyword in text:
            suggested_tags.update(tags)
            suggested_collections.update(collections)
            reasons.append(f"Keyword: {keyword}")

    if not suggested_collections and not existing_collections:
        suggested_collections.add("Inbox")
        reasons.append("No collection yet: Inbox")

    return {
        "url": url,
        "normalized_url": normalized_url,
        "domain": domain,
        "suggested_tags": sorted(suggested_tags - existing_tags),
        "suggested_collections": sorted(suggested_collections - existing_collections),
        "reasons": reasons,
        "inbox_default": not existing_collections,
    }


def domain_candidates_for(domain: str) -> list[str]:
    parts = [part for part in domain.split(".") if part]
    candidates = []
    for index in range(len(parts)):
        candidates.append(".".join(parts[index:]))
    return candidates


def clean_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def encode_list(value: list[str]) -> str:
    return "\n".join(clean_list(value))


def decode_list(value: str) -> list[str]:
    return clean_list(value.splitlines())


def add_items(existing: list[str], additions: list[str]) -> list[str]:
    return clean_list([*existing, *additions])


def remove_items(existing: list[str], removals: list[str]) -> list[str]:
    removal_set = set(clean_list(removals))
    return clean_list([item for item in existing if item not in removal_set])


def domain_for_url(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def similar_url_score(left: str, right: str) -> int:
    return round(SequenceMatcher(None, comparable_url(left), comparable_url(right)).ratio() * 100)


def comparable_url(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.netloc}{parts.path}?{parts.query}".rstrip("?")


def normalize_restore_action(value: Any) -> str:
    action = str(value or "skip").strip().lower()
    mapping = {
        "skip": "skip_existing",
        "update": "update_existing",
        "merge": "merge_existing",
        "skip_existing": "skip_existing",
        "update_existing": "update_existing",
        "merge_existing": "merge_existing",
        "create": "create",
    }
    normalized = mapping.get(action, "")
    if normalized:
        return normalized
    raise ValueError("invalid restore action")


def normalize_structure_action(value: Any, *, default: str = "reuse_existing_folder") -> str:
    action = str(value or default).strip().lower()
    mapping = {
        "reuse": "reuse_existing_folder",
        "reuse_existing_folder": "reuse_existing_folder",
        "create_parallel": "folder_create_parallel",
        "create_parallel_folder": "folder_create_parallel",
        "folder_create_parallel": "folder_create_parallel",
        "create": "folder_create",
        "folder_create": "folder_create",
    }
    normalized = mapping.get(action, "")
    if normalized:
        return normalized
    raise ValueError("invalid structure action")


def normalize_preview_decision(value: Any) -> str:
    try:
        return normalize_restore_action(value)
    except ValueError:
        return normalize_structure_action(value)


def browser_existing_index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for item in items:
        url = str(item.get("url", "")).strip()
        if not url:
            continue
        try:
            key = comparable_url(normalize_url(url))
        except ValueError:
            continue
        index.setdefault(
            key,
            {
                "id": str(item.get("id", "")),
                "title": str(item.get("title") or url),
                "url": url,
                "folder_path": str(item.get("folder_path", "")),
            },
        )
    return index


def browser_existing_folder_index(items: list[dict[str, Any]]) -> dict[str, Any]:
    by_id: dict[str, dict[str, Any]] = {}
    by_path: dict[str, dict[str, Any]] = {}
    children_by_parent: dict[str, set[str]] = {}
    for item in items:
        title = str(item.get("title", "")).strip()
        path = str(item.get("path", "")).strip()
        if not title and not path:
            continue
        parent_path = str(item.get("parent_path", "")).strip()
        folder = {
            "id": str(item.get("id", "")),
            "title": title or (path_parts(path)[-1] if path else ""),
            "path": path,
            "parent_path": parent_path,
        }
        if folder["id"]:
            by_id[folder["id"]] = folder
        if path:
            by_path[path.casefold()] = folder
        children_by_parent.setdefault(parent_path.casefold(), set()).add(folder["title"])
    return {
        "by_id": by_id,
        "by_path": by_path,
        "children_by_parent": children_by_parent,
    }


def flatten_browser_export_tree(export_tree: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for root in export_tree.get("roots", []):
        append_browser_export_record(records, root, [])
    return records


def append_browser_export_record(records: list[dict[str, Any]], node: dict[str, Any], path: list[str]) -> None:
    if node.get("type") == "bookmark" or node.get("url"):
        url = str(node.get("url", "")).strip()
        if not url:
            return
        records.append(
            {
                "id": str(node.get("id", "")),
                "title": str(node.get("title") or url),
                "url": url,
                "tags": clean_list(node.get("tags", [])),
                "collections": clean_list(node.get("collections", [])),
                "path": path,
                "source_root": str(node.get("source_root", "")),
                "source_folder_path": str(node.get("source_folder_path", "")),
                "source_position": to_int(node.get("source_position", len(records)), len(records)),
                "source_bookmark_id": str(node.get("source_bookmark_id", "")),
            }
        )
        return

    title = str(node.get("title", "")).strip()
    next_path = [*path, title] if title else path
    for child in node.get("children", []):
        append_browser_export_record(records, child, next_path)


def build_browser_restore_folder_plan(
    records: list[dict[str, Any]],
    *,
    folder_index: dict[str, Any],
    preview_id: str,
    target_mode: str,
    target_folder_id: str,
    target_title: str,
    decisions: dict[str, str],
) -> dict[str, Any]:
    by_id = folder_index.get("by_id", {})
    by_path = folder_index.get("by_path", {})
    children_by_parent = {
        key: set(values) for key, values in folder_index.get("children_by_parent", {}).items()
    }
    folder_records: list[dict[str, Any]] = []
    resolved_paths_relative: dict[tuple[str, ...], list[str]] = {}
    structure_conflict_count = 0

    selected_target = by_id.get(target_folder_id, {}) if target_folder_id else {}
    target_folder_path = path_parts(str(selected_target.get("path", "")))
    target_folder_name = str(selected_target.get("title", "")).strip()
    target_root_title = target_folder_name
    target_root_id = target_folder_id if target_mode == "existing" else ""
    target_root_path: list[str] = target_folder_path.copy() if target_mode == "existing" else []
    root_conflict_record: dict[str, Any] | None = None

    if target_mode != "existing":
        desired_root_title = str(target_title or f"LinkVault Restore").strip()
        root_record_id = folder_decision_id([], desired_root_title, kind="root")
        existing_root = by_path.get(desired_root_title.casefold())
        if existing_root:
            structure_conflict_count += 1
            action = normalize_structure_action(
                decisions.get(root_record_id),
                default="folder_create_parallel",
            )
            explicit = root_record_id in decisions
            resolved_title = (
                parallel_folder_title(desired_root_title, children_by_parent.get("".casefold(), set()))
                if action == "folder_create_parallel"
                else desired_root_title
            )
            target_root_title = resolved_title
            target_root_id = str(existing_root["id"]) if action == "reuse_existing_folder" else ""
            target_root_path = [resolved_title]
            root_conflict_record = {
                "id": root_record_id,
                "title": desired_root_title,
                "source_path": desired_root_title,
                "target_parent_path": "",
                "target_path": desired_root_title,
                "resolved_path": [],
                "resolved_path_text": resolved_title,
                "action": action,
                "available_actions": ["reuse_existing_folder", "folder_create_parallel"],
                "suggested_action": "folder_create_parallel",
                "decision_explicit": explicit,
                "existing_folder": existing_root,
                "action_preview": {
                    "reuse_existing_folder": {
                        "result_path": str(existing_root.get("path", desired_root_title)),
                        "effect": "use_existing_root",
                    },
                    "folder_create_parallel": {
                        "result_path": resolved_title,
                        "effect": "create_parallel_root",
                    },
                },
                "conflict_id": "",
            }
            folder_records.append(root_conflict_record)
        else:
            children_by_parent.setdefault("".casefold(), set()).add(desired_root_title)
            target_root_title = desired_root_title
            target_root_path = [desired_root_title]

    unique_paths: list[list[str]] = []
    seen_paths: set[tuple[str, ...]] = set()
    for record in records:
        relative_path = adjusted_restore_path(record["path"], target_mode, target_folder_name)
        for index in range(1, len(relative_path) + 1):
            prefix = tuple(relative_path[:index])
            if prefix in seen_paths:
                continue
            seen_paths.add(prefix)
            unique_paths.append(list(prefix))

    for source_prefix in unique_paths:
        title = source_prefix[-1]
        parent_source_prefix = tuple(source_prefix[:-1])
        parent_resolved_relative = resolved_paths_relative.get(parent_source_prefix, [])
        parent_absolute = [*target_root_path, *parent_resolved_relative]
        parent_path_text = " / ".join(parent_absolute)
        candidate_path = [*parent_absolute, title]
        existing_folder = by_path.get(" / ".join(candidate_path).casefold())
        action = "folder_create"
        explicit = False
        conflict_id = ""
        available_actions = ["folder_create"]
        resolved_title = title
        if existing_folder:
            structure_conflict_count += 1
            folder_record_id = folder_decision_id(parent_absolute, title)
            action = normalize_structure_action(
                decisions.get(folder_record_id),
                default="reuse_existing_folder",
            )
            explicit = folder_record_id in decisions
            available_actions = ["reuse_existing_folder", "folder_create_parallel"]
            if action == "folder_create_parallel":
                resolved_title = parallel_folder_title(title, children_by_parent.get(parent_path_text.casefold(), set()))
            resolved_relative = [*parent_resolved_relative, resolved_title]
            resolved_absolute = [*target_root_path, *resolved_relative]
            folder_records.append(
                {
                    "id": folder_record_id,
                    "title": title,
                    "source_path": " / ".join(source_prefix),
                    "target_parent_path": parent_path_text,
                    "target_path": " / ".join(candidate_path),
                    "resolved_path": resolved_relative,
                    "resolved_path_text": " / ".join(resolved_absolute),
                    "action": action,
                    "available_actions": available_actions,
                    "suggested_action": "reuse_existing_folder",
                    "decision_explicit": explicit,
                    "existing_folder": existing_folder,
                    "action_preview": {
                        "reuse_existing_folder": {
                            "result_path": " / ".join(candidate_path),
                            "effect": "reuse_existing_folder",
                        },
                        "folder_create_parallel": {
                            "result_path": " / ".join(resolved_absolute),
                            "effect": "create_parallel_folder",
                        },
                    },
                    "conflict_id": conflict_id,
                }
            )
        resolved_relative = [*parent_resolved_relative, resolved_title]
        resolved_paths_relative[tuple(source_prefix)] = resolved_relative
        children_by_parent.setdefault(parent_path_text.casefold(), set()).add(resolved_title)

    for record in records:
        relative_path = adjusted_restore_path(record["path"], target_mode, target_folder_name)
        resolved_paths_relative[tuple(record["path"])] = resolved_paths_relative.get(tuple(relative_path), relative_path)

    return {
        "folder_records": folder_records,
        "resolved_paths": resolved_paths_relative,
        "structure_conflict_count": structure_conflict_count,
        "target_root": {
            "title": target_root_title,
            "id": target_root_id,
            "path": " / ".join(target_root_path),
            "reuse_existing": bool(target_root_id),
        },
    }


def adjusted_restore_path(path: list[str], target_mode: str, target_folder_name: str) -> list[str]:
    clean_path = [str(part).strip() for part in path if str(part).strip()]
    if target_mode != "existing" or not clean_path:
        return clean_path
    if target_folder_name and clean_path[0].casefold() == target_folder_name.casefold():
        return clean_path[1:]
    return clean_path


def folder_decision_id(parent_resolved: list[str], title: str, *, kind: str = "folder") -> str:
    parent_text = " / ".join(parent_resolved)
    return f"{kind}::{parent_text}::{title}"


def parallel_folder_title(title: str, sibling_titles: set[str]) -> str:
    suffix = f"{title} (LinkVault)"
    if suffix not in sibling_titles:
        return suffix
    index = 2
    while True:
        candidate = f"{title} (LinkVault {index})"
        if candidate not in sibling_titles:
            return candidate
        index += 1


def group_differences(items: list[dict[str, Any]], winner_id: str) -> list[dict[str, Any]]:
    fields = ["url", "title", "description", "tags", "collections", "notes", "favorite", "pinned"]
    winner = next(item for item in items if item["id"] == winner_id)
    differences = []
    for field in fields:
        values = [{"id": item["id"], "value": item[field]} for item in items]
        comparable_values = {jsonish_value(item[field]) for item in items}
        if len(comparable_values) <= 1:
            continue
        differences.append(
            {
                "field": field,
                "winner_value": winner[field],
                "values": values,
            }
        )
    return differences


def jsonish_value(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    return str(value)


def merge_notes(winner: Bookmark, losers: list[Bookmark]) -> str:
    parts = [winner.notes.strip()] if winner.notes.strip() else []
    for loser in losers:
        if not loser.notes.strip():
            continue
        parts.append(f"Merged from {loser.id}: {loser.notes.strip()}")
    return "\n\n".join(parts)


def to_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def choose_winner(bookmarks: list[Bookmark]) -> Bookmark:
    return sorted(
        bookmarks,
        key=lambda bookmark: (
            bookmark.pinned,
            bookmark.favorite,
            bool(bookmark.notes),
            len(bookmark.tags),
            len(bookmark.collections),
            bookmark.created_at,
        ),
        reverse=True,
    )[0]


def winner_reason_label(winner: dict[str, Any], all_items: list[dict[str, Any]]) -> str:
    """Return a short human-readable string explaining why this bookmark was chosen as winner."""
    reasons = []
    if winner.get("pinned"):
        reasons.append("gepinnt")
    if winner.get("favorite"):
        reasons.append("Favorit")
    if winner.get("notes"):
        reasons.append("hat Notizen")
    winner_tags = len(winner.get("tags") or [])
    max_tags = max((len(item.get("tags") or []) for item in all_items), default=0)
    if winner_tags > 0 and winner_tags >= max_tags:
        reasons.append(f"{winner_tags} Tag{'s' if winner_tags != 1 else ''}")
    winner_colls = len(winner.get("collections") or [])
    max_colls = max((len(item.get("collections") or []) for item in all_items), default=0)
    if winner_colls > 0 and winner_colls >= max_colls and "Tags" not in " ".join(reasons):
        reasons.append(f"{winner_colls} Collection{'s' if winner_colls != 1 else ''}")
    if not reasons:
        reasons.append("ältestes Bookmark")
    return ", ".join(reasons)


def browser_export_sort_key(bookmark: Bookmark) -> tuple[str, str, int, str]:
    return (
        bookmark.source_root or "LinkVault",
        bookmark.source_folder_path or "/".join(bookmark.collections),
        bookmark.source_position if bookmark.source_position >= 0 else 999_999,
        bookmark.title.lower(),
    )


def export_folder_path(bookmark: Bookmark) -> list[str]:
    if bookmark.source_folder_path.strip():
        parts = path_parts(bookmark.source_folder_path)
        if parts and bookmark.source_root.strip() and parts[0] == bookmark.source_root.strip():
            return parts[1:]
        return parts
    if bookmark.collections:
        return bookmark.collections
    return ["Inbox"]


def path_parts(value: str) -> list[str]:
    delimiter = " / " if " / " in value else "/"
    return [part.strip() for part in value.split(delimiter) if part.strip()]


def strip_internal_folder_maps(node: dict[str, Any]) -> dict[str, Any]:
    return {
        key: [strip_internal_folder_maps(child) for child in value] if key == "children" else value
        for key, value in node.items()
        if key != "_folders"
    }


def parse_browser_html(html: str) -> list[dict[str, Any]]:
    parser = BrowserBookmarkParser()
    parser.feed(html)
    return parser.items


def normalize_browser_bookmark_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise ValueError("items must be a list")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "")).strip()
        title = str(item.get("title") or url).strip()
        source_root = str(item.get("source_root", "")).strip()
        source_folder_path = str(item.get("source_folder_path", "")).strip()
        folder_path = clean_list(item.get("collections", []))
        if not folder_path and source_folder_path:
            folder_path = path_parts(source_folder_path)
        normalized.append(
            {
                "url": url,
                "title": title or url,
                "description": str(item.get("description", "")),
                "tags": clean_list(item.get("tags", [])),
                "collections": folder_path or ["Inbox"],
                "favorite": to_bool(item.get("favorite", False)),
                "pinned": to_bool(item.get("pinned", False)),
                "notes": str(item.get("notes", "")),
                "source_browser": str(item.get("source_browser", "browser")).strip() or "browser",
                "source_root": source_root,
                "source_folder_path": source_folder_path or " / ".join(folder_path),
                "source_position": to_int(item.get("source_position", item.get("index", index)), index),
                "source_bookmark_id": str(item.get("source_bookmark_id", item.get("id", ""))).strip(),
            }
        )
    return normalized


def parse_chromium_json(data: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid Chromium bookmarks JSON.") from exc

    roots = payload.get("roots") if isinstance(payload, dict) else None
    if not isinstance(roots, dict):
        raise ValueError("Chromium bookmarks JSON must contain a roots object.")

    items: list[dict[str, Any]] = []
    for key in ["bookmark_bar", "other", "synced", "mobile"]:
        node = roots.get(key)
        if isinstance(node, dict):
            root_name = str(node.get("name") or chromium_root_label(key)).strip()
            walk_chromium_bookmark_node(
                node,
                [root_name] if root_name else [],
                items,
                source_root=root_name,
                source_browser="chromium",
            )

    return items


def parse_firefox_json(data: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid Firefox bookmarks JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Firefox bookmarks JSON must contain an object.")

    items: list[dict[str, Any]] = []
    walk_firefox_bookmark_node(payload, [], items, source_root="", source_browser="firefox")
    return items


def walk_firefox_bookmark_node(
    node: dict[str, Any],
    folder_path: list[str],
    items: list[dict[str, Any]],
    *,
    source_root: str,
    source_browser: str,
    position: int = 0,
) -> None:
    node_type = str(node.get("type", "")).lower()
    url = str(node.get("uri") or node.get("url") or "").strip()
    title = str(node.get("title") or url).strip()

    if node_type in {"text/x-moz-place", "url"} and url:
        tags = clean_list(node.get("tags", []))
        keyword = str(node.get("keyword", "")).strip()
        if keyword:
            tags = clean_list([*tags, keyword])
        items.append(
            {
                "url": url,
                "title": title or url,
                "tags": tags,
                "collections": folder_path,
                "source_browser": source_browser,
                "source_root": source_root or (folder_path[0] if folder_path else ""),
                "source_folder_path": " / ".join(folder_path),
                "source_position": position,
                "source_bookmark_id": str(node.get("guid") or node.get("id") or ""),
            }
        )
        return

    children = node.get("children", [])
    if not isinstance(children, list):
        return

    next_path = folder_path
    if title and node_type in {"text/x-moz-place-container", "folder", ""} and title.lower() not in {"root", "places"}:
        next_path = [*folder_path, title]
        if not source_root:
            source_root = title

    for child_position, child in enumerate(children):
        if isinstance(child, dict):
            walk_firefox_bookmark_node(
                child,
                next_path,
                items,
                source_root=source_root,
                source_browser=source_browser,
                position=child_position,
            )


def parse_safari_zip(data: str) -> list[dict[str, Any]]:
    try:
        archive_bytes = base64.b64decode(data, validate=True)
    except ValueError as exc:
        raise ValueError("Safari ZIP import expects base64 encoded ZIP data.") from exc

    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            bookmark_name = safari_bookmarks_name(archive.namelist())
            with archive.open(bookmark_name) as bookmark_file:
                html = bookmark_file.read().decode("utf-8", errors="replace")
    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid Safari ZIP archive.") from exc
    except KeyError as exc:
        raise ValueError("Safari ZIP archive must contain Bookmarks.html.") from exc

    return parse_browser_html(html)


def safari_bookmarks_name(names: list[str]) -> str:
    for name in names:
        if name.rsplit("/", 1)[-1].lower() == "bookmarks.html":
            return name
    raise KeyError("Bookmarks.html")


def walk_chromium_bookmark_node(
    node: dict[str, Any],
    folder_path: list[str],
    items: list[dict[str, Any]],
    *,
    source_root: str,
    source_browser: str,
    position: int = 0,
) -> None:
    node_type = str(node.get("type", "")).lower()
    url = str(node.get("url", "")).strip()
    name = str(node.get("name") or url).strip()

    if node_type == "url" and url:
        items.append(
            {
                "url": url,
                "title": name or url,
                "collections": folder_path,
                "source_browser": source_browser,
                "source_root": source_root,
                "source_folder_path": " / ".join(folder_path),
                "source_position": position,
                "source_bookmark_id": str(node.get("id", "")),
            }
        )
        return

    children = node.get("children", [])
    if not isinstance(children, list):
        return

    next_path = folder_path
    if node_type == "folder" and name and (not folder_path or folder_path[-1] != name):
        next_path = [*folder_path, name]

    for child_position, child in enumerate(children):
        if isinstance(child, dict):
            walk_chromium_bookmark_node(
                child,
                next_path,
                items,
                source_root=source_root,
                source_browser=source_browser,
                position=child_position,
            )


def chromium_root_label(key: str) -> str:
    return {
        "bookmark_bar": "Bookmarks Bar",
        "other": "Other Bookmarks",
        "synced": "Mobile Bookmarks",
        "mobile": "Mobile Bookmarks",
    }.get(key, key)


class BrowserBookmarkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[dict[str, Any]] = []
        self.folder_stack: list[str] = []
        self.pending_folder: str | None = None
        self.current_tag: str | None = None
        self.current_link: dict[str, Any] | None = None
        self.text_parts: list[str] = []
        self.root_depth_seen = False
        self.position_stack: list[int] = [0]
        # Safari Reading List tracking
        self._pending_reading_list: bool = False
        self._reading_list_folder_depths: list[bool] = [False]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag == "h3":
            self.current_tag = "h3"
            self.text_parts = []
            self._pending_reading_list = attrs_dict.get("reading_list", "").upper() == "TRUE"
        elif tag == "a" and "href" in attrs_dict:
            self.current_tag = "a"
            raw_tags = attrs_dict.get("tags", "")
            base_tags = [t.strip() for t in raw_tags.split(",") if t.strip()] if raw_tags else []
            is_reading = (
                self._pending_reading_list
                or self._reading_list_folder_depths[-1]
                or attrs_dict.get("toreadlist", "").upper() == "TRUE"
            )
            if is_reading and "reading-list" not in base_tags:
                base_tags = [*base_tags, "reading-list"]
            self.current_link = {
                "url": attrs_dict["href"],
                "tags": base_tags,
                "collections": list(self.folder_stack),
                "source_browser": "browser-html",
                "source_root": self.folder_stack[0] if self.folder_stack else "",
                "source_folder_path": " / ".join(self.folder_stack),
                "source_position": self.position_stack[-1] if self.position_stack else 0,
            }
            self.text_parts = []
        elif tag == "dl":
            if self.pending_folder:
                self.folder_stack.append(self.pending_folder)
                self.pending_folder = None
                self.position_stack.append(0)
                self._reading_list_folder_depths.append(self._pending_reading_list)
                self._pending_reading_list = False
            elif not self.root_depth_seen:
                self.root_depth_seen = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "h3" and self.current_tag == "h3":
            folder_name = " ".join("".join(self.text_parts).split())
            self.pending_folder = folder_name or None
            self.current_tag = None
        elif tag == "a" and self.current_tag == "a" and self.current_link:
            title = " ".join("".join(self.text_parts).split())
            self.current_link["title"] = title or self.current_link["url"]
            self.items.append(self.current_link)
            if self.position_stack:
                self.position_stack[-1] += 1
            self.current_link = None
            self.current_tag = None
        elif tag == "dl" and self.folder_stack:
            self.folder_stack.pop()
            if len(self.position_stack) > 1:
                self.position_stack.pop()
            if len(self._reading_list_folder_depths) > 1:
                self._reading_list_folder_depths.pop()

    def handle_data(self, data: str) -> None:
        if self.current_tag in {"a", "h3"}:
            self.text_parts.append(data)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# linkding import (JSON export format)
# ---------------------------------------------------------------------------

def parse_linkding_json(data: str) -> list[dict[str, Any]]:
    """Parse a linkding JSON export.

    linkding's export format (``/api/bookmarks/?format=json`` or the UI export)
    is a paginated DRF response: ``{"count": N, "results": [...]}`` where each
    result has at minimum ``url``, ``title``, ``description``, ``tag_names``
    (list of strings) and ``website_title`` / ``website_description``.
    The UI HTML export is also supported via ``parse_browser_html``; this
    function handles the JSON path only.
    """
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON for linkding import.") from exc

    # Accept paginated DRF response or bare list
    if isinstance(payload, dict):
        results = payload.get("results") or payload.get("bookmarks") or []
        if not isinstance(results, list):
            results = []
    elif isinstance(payload, list):
        results = payload
    else:
        raise ValueError("linkding JSON must contain an object with 'results' or a list.")

    items: list[dict[str, Any]] = []
    for entry in results:
        if not isinstance(entry, dict):
            continue
        url = str(entry.get("url", "")).strip()
        if not url:
            continue
        # Prefer explicit title, fall back to website_title
        title = (
            str(entry.get("title", "")).strip()
            or str(entry.get("website_title", "")).strip()
        )
        description = (
            str(entry.get("description", "")).strip()
            or str(entry.get("website_description", "")).strip()
        )
        raw_tags = entry.get("tag_names", [])
        tags: list[str] = [str(t).strip() for t in raw_tags if str(t).strip()] if isinstance(raw_tags, list) else []
        notes = str(entry.get("notes", "")).strip()
        is_archived = bool(entry.get("is_archived", False))
        archive_status = "archived" if is_archived else ""
        items.append(
            {
                "url": url,
                "title": title or url,
                "description": description,
                "tags": tags,
                "collections": [],  # linkding has no folders; tags carry structure
                "notes": notes,
                "archive_status": archive_status,
                "source_browser": "linkding",
                "source_root": "",
                "source_folder_path": "",
                "source_position": len(items),
                "source_bookmark_id": str(entry.get("id", "")),
            }
        )
    return items


# ---------------------------------------------------------------------------
# MozLZ4 decompression (Firefox .jsonlz4 backup files)
# ---------------------------------------------------------------------------

MOZLZ4_MAGIC = b"mozLz40\0"
_MOZLZ4_HEADER_LEN = len(MOZLZ4_MAGIC)  # 8 bytes


def _lz4_block_decompress(src: bytes, max_output: int = 64 * 1024 * 1024) -> bytes:
    """Pure-Python LZ4 block decompressor (no frame header expected)."""
    out = bytearray()
    pos = 0
    n = len(src)
    while pos < n:
        token = src[pos]
        pos += 1
        lit_len = (token >> 4) & 0xF
        if lit_len == 15:
            while pos < n:
                extra = src[pos]
                pos += 1
                lit_len += extra
                if extra != 255:
                    break
        out.extend(src[pos : pos + lit_len])
        pos += lit_len
        if pos >= n:
            break  # last sequence has no match
        if pos + 2 > n:
            raise ValueError("Truncated LZ4 match offset.")
        offset = struct.unpack_from("<H", src, pos)[0]
        pos += 2
        if offset == 0:
            raise ValueError("Invalid LZ4 match offset 0.")
        match_len = (token & 0xF) + 4
        if match_len == 4 + 15:
            while pos < n:
                extra = src[pos]
                pos += 1
                match_len += extra
                if extra != 255:
                    break
        match_start = len(out) - offset
        if match_start < 0:
            raise ValueError("LZ4 match offset out of bounds.")
        for i in range(match_len):
            out.append(out[match_start + i])
        if len(out) > max_output:
            raise ValueError("LZ4 decompressed output exceeds safety limit.")
    return bytes(out)


def decompress_mozlz4(raw: bytes) -> bytes:
    """Strip MozLZ4 magic header and decompress LZ4 block data."""
    if not raw.startswith(MOZLZ4_MAGIC):
        raise ValueError("Not a MozLZ4 file (magic header missing).")
    return _lz4_block_decompress(raw[_MOZLZ4_HEADER_LEN:])


def parse_firefox_jsonlz4(data: str) -> list[dict[str, Any]]:
    """Parse a Firefox .jsonlz4 backup supplied as base64."""
    try:
        raw = base64.b64decode(data, validate=True)
    except Exception as exc:
        raise ValueError("Firefox JSONLZ4 import expects base64-encoded binary data.") from exc
    try:
        decompressed = decompress_mozlz4(raw)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to decompress MozLZ4 data: {exc}") from exc
    return parse_firefox_json(decompressed.decode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Generic CSV / JSON import
# ---------------------------------------------------------------------------

_GENERIC_FIELD_CANDIDATES: dict[str, list[str]] = {
    "url": ["url", "uri", "href", "link", "address"],
    "title": ["title", "name", "label", "description", "text"],
    "tags": ["tags", "tag", "keywords", "labels", "categories"],
    "collections": ["collections", "collection", "folder", "folders", "group", "groups"],
    "description": ["description", "desc", "summary", "note", "excerpt", "abstract"],
    "notes": ["notes", "note", "comment", "memo"],
}


def _best_field_match(headers: list[str], candidates: list[str]) -> str | None:
    lc_headers = [h.lower().strip() for h in headers]
    for c in candidates:
        if c in lc_headers:
            return headers[lc_headers.index(c)]
    return None


def infer_generic_columns(headers: list[str]) -> dict[str, str | None]:
    """Return best-guess field mapping for a list of column headers."""
    return {
        field: _best_field_match(headers, candidates)
        for field, candidates in _GENERIC_FIELD_CANDIDATES.items()
    }


def parse_generic_csv(data: str, mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Parse generic CSV bookmark export using a caller-supplied field mapping."""
    url_field = mapping.get("url") or ""
    if not url_field:
        raise ValueError("url_field is required for generic CSV import.")
    reader = csv.DictReader(io.StringIO(data))
    items: list[dict[str, Any]] = []
    for row in reader:
        url = str(row.get(url_field, "")).strip()
        if not url:
            continue
        title_field = mapping.get("title") or ""
        tags_field = mapping.get("tags") or ""
        col_field = mapping.get("collections") or ""
        desc_field = mapping.get("description") or ""
        notes_field = mapping.get("notes") or ""
        raw_tags = str(row.get(tags_field, "")) if tags_field else ""
        tags = [t.strip() for t in raw_tags.replace(";", ",").split(",") if t.strip()]
        raw_cols = str(row.get(col_field, "")) if col_field else ""
        collections = [c.strip() for c in raw_cols.replace(";", ",").split(",") if c.strip()]
        items.append(
            {
                "url": url,
                "title": str(row.get(title_field, "")).strip() if title_field else "",
                "tags": tags,
                "collections": collections,
                "description": str(row.get(desc_field, "")).strip() if desc_field else "",
                "notes": str(row.get(notes_field, "")).strip() if notes_field else "",
                "source_browser": "generic-csv",
                "source_root": "",
                "source_folder_path": " / ".join(collections),
                "source_position": len(items),
                "source_bookmark_id": "",
            }
        )
    return items


def parse_generic_json(data: str, mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Parse generic JSON bookmark export using a caller-supplied field mapping."""
    url_field = mapping.get("url") or ""
    if not url_field:
        raise ValueError("url_field is required for generic JSON import.")
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON for generic import.") from exc
    # Accept top-level list or dict with a list value
    rows: list[Any] = []
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        for v in payload.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                rows = v
                break
        if not rows:
            rows = [payload]
    items: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get(url_field, "")).strip()
        if not url:
            continue
        title_field = mapping.get("title") or ""
        tags_field = mapping.get("tags") or ""
        col_field = mapping.get("collections") or ""
        desc_field = mapping.get("description") or ""
        notes_field = mapping.get("notes") or ""
        raw_tags = row.get(tags_field, []) if tags_field else []
        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.replace(";", ",").split(",") if t.strip()]
        elif isinstance(raw_tags, list):
            tags = [str(t).strip() for t in raw_tags if str(t).strip()]
        else:
            tags = []
        raw_cols = row.get(col_field, []) if col_field else []
        if isinstance(raw_cols, str):
            collections = [c.strip() for c in raw_cols.replace(";", ",").split(",") if c.strip()]
        elif isinstance(raw_cols, list):
            collections = [str(c).strip() for c in raw_cols if str(c).strip()]
        else:
            collections = []
        items.append(
            {
                "url": url,
                "title": str(row.get(title_field, "")).strip() if title_field else "",
                "tags": tags,
                "collections": collections,
                "description": str(row.get(desc_field, "")).strip() if desc_field else "",
                "notes": str(row.get(notes_field, "")).strip() if notes_field else "",
                "source_browser": "generic-json",
                "source_root": "",
                "source_folder_path": " / ".join(collections),
                "source_position": len(items),
                "source_bookmark_id": str(row.get("id", row.get("guid", ""))),
            }
        )
    return items
