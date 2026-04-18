from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .url_tools import normalize_url


@dataclass
class Bookmark:
    id: str
    url: str
    normalized_url: str
    title: str
    tags: list[str] = field(default_factory=list)
    collections: list[str] = field(default_factory=list)
    favorite: bool = False
    pinned: bool = False
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class BookmarkStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[Bookmark]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [Bookmark(**item) for item in payload.get("bookmarks", [])]

    def add(self, payload: dict[str, Any]) -> Bookmark:
        url = str(payload.get("url", "")).strip()
        normalized_url = normalize_url(url)
        now = datetime.now(UTC).isoformat()
        bookmark = Bookmark(
            id=uuid4().hex,
            url=url,
            normalized_url=normalized_url,
            title=str(payload.get("title") or url),
            tags=clean_list(payload.get("tags", [])),
            collections=clean_list(payload.get("collections", [])),
            favorite=bool(payload.get("favorite", False)),
            pinned=bool(payload.get("pinned", False)),
            notes=str(payload.get("notes", "")),
            created_at=now,
            updated_at=now,
        )
        bookmarks = self.list()
        bookmarks.append(bookmark)
        self.save(bookmarks)
        return bookmark

    def save(self, bookmarks: list[Bookmark]) -> None:
        payload = {"bookmarks": [asdict(bookmark) for bookmark in bookmarks]}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

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
                    "items": [asdict(bookmark) for bookmark in bookmarks],
                }
            )
        return result


def clean_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def choose_winner(bookmarks: list[Bookmark]) -> Bookmark:
    return sorted(
        bookmarks,
        key=lambda bookmark: (
            bookmark.pinned,
            bookmark.favorite,
            bool(bookmark.notes),
            len(bookmark.tags),
            bookmark.created_at,
        ),
        reverse=True,
    )[0]
