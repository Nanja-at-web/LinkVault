from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "mkt_tok",
    "msclkid",
}


def normalize_url(raw_url: str) -> str:
    """Return a stable URL fingerprint for deduplication."""
    raw_url = raw_url.strip()
    if not raw_url:
        raise ValueError("url is required")

    if "://" not in raw_url:
        raw_url = f"https://{raw_url}"

    parts = urlsplit(raw_url)
    scheme = (parts.scheme or "https").lower()
    host = (parts.hostname or "").lower()
    if not host:
        raise ValueError("url host is required")

    port = parts.port
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"

    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query_pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        key_lower = key.lower()
        if key_lower.startswith("utm_") or key_lower in TRACKING_PARAMS:
            continue
        query_pairs.append((key, value))

    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))
