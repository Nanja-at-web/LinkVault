from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import urlsplit
from uuid import uuid4

from .metadata import PageMetadata, fetch_url_metadata
from .url_tools import normalize_url


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
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BookmarkFilters:
    favorite: bool | None = None
    pinned: bool | None = None
    domain: str = ""
    tag: str = ""
    collection: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


MetadataFetcher = Callable[[str], PageMetadata]


class BookmarkStore:
    def __init__(self, path: Path, metadata_fetcher: MetadataFetcher | None = fetch_url_metadata) -> None:
        self.path = path
        self.metadata_fetcher = metadata_fetcher
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
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
            connection.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_normalized_url ON bookmarks(normalized_url)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_domain ON bookmarks(domain)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_status ON bookmarks(status)")
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
        filter_sql.insert(0, "b.status = 'active'")
        where = f"WHERE {' AND '.join(filter_sql)}"
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM bookmarks b
                {where}
                ORDER BY favorite DESC, pinned DESC, created_at DESC, title ASC
                """,
                values,
            ).fetchall()
        return [bookmark_from_row(row) for row in rows]

    def search(self, query: str, filters: BookmarkFilters | None = None) -> list[Bookmark]:
        fts_query = build_fts_query(query)
        if not fts_query:
            return self.list(filters=filters)

        filter_sql, filter_values = bookmark_filter_sql(filters or BookmarkFilters())
        clauses = ["bookmarks_fts MATCH ?", "b.status = 'active'", *filter_sql]
        values: list[Any] = [fts_query, *filter_values]
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT b.*, bm25(bookmarks_fts) AS search_rank
                FROM bookmarks_fts
                JOIN bookmarks b ON b.id = bookmarks_fts.bookmark_id
                WHERE {' AND '.join(clauses)}
                ORDER BY search_rank ASC, b.favorite DESC, b.pinned DESC, b.updated_at DESC, b.title ASC
                """,
                values,
            ).fetchall()
        return [bookmark_from_row(row) for row in rows]

    def get(self, bookmark_id: str) -> Bookmark | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)).fetchone()
        return bookmark_from_row(row) if row else None

    def add(self, payload: dict[str, Any], *, enrich_metadata: bool = True) -> Bookmark:
        now = datetime.now(UTC).isoformat()
        payload = self.with_metadata(payload, enrich_metadata=enrich_metadata)
        bookmark = bookmark_from_payload(payload, bookmark_id=uuid4().hex, created_at=now, updated_at=now)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO bookmarks (
                    id, url, normalized_url, title, description, domain, favicon_url, tags, collections,
                    favorite, pinned, notes, status, merged_into, merged_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    status = ?, merged_into = ?, merged_at = ?, updated_at = ?
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
        updated_winner = self.update(winner_id, updated_winner_payload, enrich_metadata=False)
        if not updated_winner:
            raise ValueError("winner not found")

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

        merged_losers = [bookmark for loser in losers if (bookmark := self.get(loser.id))]

        return {
            "winner": updated_winner.to_dict(),
            "merged_losers": [bookmark.to_dict() for bookmark in merged_losers],
            "merged_count": len(merged_losers),
            "deleted": 0,
        }

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
            connection.execute("DELETE FROM bookmarks_fts WHERE bookmark_id = ?", (bookmark_id,))
            cursor = connection.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        return cursor.rowcount > 0

    def import_browser_html(self, html: str) -> dict[str, Any]:
        parser = BrowserBookmarkParser()
        parser.feed(html)
        created = 0
        duplicates = 0
        imported: list[Bookmark] = []
        existing_urls = {bookmark.normalized_url for bookmark in self.list()}

        for item in parser.items:
            normalized_url = normalize_url(item["url"])
            if normalized_url in existing_urls:
                duplicates += 1
                continue
            bookmark = self.add(item)
            existing_urls.add(bookmark.normalized_url)
            imported.append(bookmark)
            created += 1

        return {
            "created": created,
            "duplicates_skipped": duplicates,
            "bookmarks": [bookmark.to_dict() for bookmark in imported],
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

    def sync_search_index(self, connection: sqlite3.Connection) -> None:
        bookmark_count = connection.execute("SELECT COUNT(*) FROM bookmarks WHERE status = 'active'").fetchone()[0]
        fts_count = connection.execute("SELECT COUNT(*) FROM bookmarks_fts").fetchone()[0]
        if bookmark_count != fts_count:
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
    return Bookmark(
        id=bookmark_id,
        url=url,
        normalized_url=normalized_url,
        title=title or url,
        description=str(payload.get("description", "")),
        domain=domain_for_url(normalized_url),
        favicon_url=str(payload.get("favicon_url", "")),
        tags=clean_list(payload.get("tags", [])),
        collections=clean_list(payload.get("collections", [])),
        favorite=to_bool(payload.get("favorite", False)),
        pinned=to_bool(payload.get("pinned", False)),
        notes=str(payload.get("notes", "")),
        status=str(payload.get("status", "active")),
        merged_into=str(payload.get("merged_into", "")),
        merged_at=str(payload.get("merged_at", "")),
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
        created_at=row["created_at"],
        updated_at=row["updated_at"],
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
        bookmark.created_at,
        bookmark.updated_at,
    )


def upsert_search_index(connection: sqlite3.Connection, bookmark: Bookmark) -> None:
    connection.execute("DELETE FROM bookmarks_fts WHERE bookmark_id = ?", (bookmark.id,))
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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag == "h3":
            self.current_tag = "h3"
            self.text_parts = []
        elif tag == "a" and "href" in attrs_dict:
            self.current_tag = "a"
            self.current_link = {
                "url": attrs_dict["href"],
                "tags": attrs_dict.get("tags", ""),
                "collections": list(self.folder_stack),
            }
            self.text_parts = []
        elif tag == "dl":
            if self.pending_folder:
                self.folder_stack.append(self.pending_folder)
                self.pending_folder = None
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
            self.current_link = None
            self.current_tag = None
        elif tag == "dl" and self.folder_stack:
            self.folder_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.current_tag in {"a", "h3"}:
            self.text_parts.append(data)
