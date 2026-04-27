from __future__ import annotations

import ssl
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass
class PageMetadata:
    title: str = ""
    description: str = ""
    favicon_url: str = ""
    final_url: str = ""


def fetch_url_metadata(url: str, timeout: float = 5.0) -> PageMetadata:
    request = Request(
        url,
        headers={
            "User-Agent": "LinkVault/0.1 metadata fetcher",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        return fetch_request_metadata(request, timeout=timeout)
    except URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        print(f"[LinkVault] SSL certificate verification failed for {url!r}, retrying without verification", file=sys.stderr)
        insecure_context = ssl._create_unverified_context()
        return fetch_request_metadata(request, timeout=timeout, context=insecure_context)


def fetch_request_metadata(
    request: Request,
    *,
    timeout: float,
    context: ssl.SSLContext | None = None,
) -> PageMetadata:
    with urlopen(request, timeout=timeout, context=context) as response:
        final_url = response.geturl()
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            return PageMetadata(final_url=final_url)
        body = response.read(1_000_000)
        charset = response.headers.get_content_charset() or "utf-8"

    parser = MetadataParser(final_url)
    parser.feed(body.decode(charset, errors="replace"))
    return parser.metadata()


class MetadataParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.favicon_url = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = attrs_dict.get("property") or attrs_dict.get("name")
            content = attrs_dict.get("content", "")
            if key and content:
                self.meta[key.lower()] = " ".join(content.split())
        elif tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            href = attrs_dict.get("href", "")
            if href and not self.favicon_url and ("icon" in rel or rel == "shortcut icon"):
                self.favicon_url = urljoin(self.base_url, href)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    def metadata(self) -> PageMetadata:
        title = self.meta.get("og:title") or self.meta.get("twitter:title") or " ".join(
            "".join(self.title_parts).split()
        )
        description = (
            self.meta.get("description")
            or self.meta.get("og:description")
            or self.meta.get("twitter:description")
            or ""
        )
        return PageMetadata(
            title=title,
            description=description,
            favicon_url=self.favicon_url or urljoin(self.base_url, "/favicon.ico"),
            final_url=self.base_url,
        )


def check_url_health(url: str, timeout: float = 5.0) -> dict[str, Any]:
    """Light health check for a single URL.

    Tries HEAD first (cheap), falls back to GET if HEAD is not supported.
    On SSL errors retries without certificate verification.
    Returns dict with keys: ok (bool), status_code (int), error (str).
    """
    result: dict[str, Any] = {"ok": False, "status_code": 0, "error": ""}

    def _attempt(method: str, ctx: ssl.SSLContext | None = None) -> bool:
        req = Request(
            url,
            method=method,
            headers={"User-Agent": "LinkVault/0.1 link-checker"},
        )
        try:
            with urlopen(req, timeout=timeout, context=ctx) as resp:
                result["status_code"] = resp.status
                result["ok"] = resp.status < 400
                result["error"] = ""
                return True
        except HTTPError as exc:
            result["status_code"] = exc.code
            result["ok"] = exc.code < 400
            result["error"] = f"HTTP {exc.code}" if exc.code >= 400 else ""
            return True
        except URLError as exc:
            result["error"] = str(exc.reason)
            return False

    reached = _attempt("HEAD")
    if not reached or result["status_code"] == 405:
        # HEAD not supported or unreachable — try GET
        result.update({"ok": False, "status_code": 0, "error": ""})
        reached = _attempt("GET")

    if not reached and "CERTIFICATE_VERIFY_FAILED" in result.get("error", ""):
        insecure = ssl._create_unverified_context()
        result.update({"ok": False, "status_code": 0, "error": ""})
        if not _attempt("HEAD", insecure):
            _attempt("GET", insecure)

    return result
