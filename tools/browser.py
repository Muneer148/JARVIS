"""
tools/browser.py
=================
Fetch a web page and return its readable text content to the JARVIS agent.

Static, public-web-only browser fetcher with SSRF protection and response
limits. JavaScript rendering, authentication, crawling, and sessions remain
out of scope for this V1 tool.
"""

from __future__ import annotations

import ipaddress
import os
import re
import socket
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

_TIMEOUT = float(os.environ.get("JARVIS_BROWSER_TIMEOUT", "12"))
_MAX_BYTES = int(os.environ.get("JARVIS_BROWSER_MAX_BYTES", str(2_000_000)))
_MAX_TEXT = int(os.environ.get("JARVIS_BROWSER_MAX_TEXT_CHARS", "8000"))
_MAX_LINKS = 25
_MAX_REDIRECTS = 5

_USER_AGENT = "Mozilla/5.0 (compatible; JARVIS-personal-agent/1.0)"
_NOISE_TAGS = frozenset({"script", "style", "nav", "header", "footer", "noscript", "svg", "aside"})
_BLOCK_TAGS = frozenset({"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "blockquote", "section", "article", "pre", "code"})


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._title_parts: list[str] = []
        self._in_title = False
        self._noise_depth = 0
        self._chunks: list[str] = []
        self._link_href: str | None = None
        self._link_parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in _NOISE_TAGS:
            self._noise_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "a" and not self._noise_depth:
            href = attrs_dict.get("href")
            if href:
                self._link_href = href
                self._link_parts = []
        elif tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _NOISE_TAGS:
            self._noise_depth = max(0, self._noise_depth - 1)
        elif tag == "title":
            self._in_title = False
        elif tag == "a" and self._link_href is not None:
            text = "".join(self._link_parts).strip()
            if text:
                self.links.append((text, self._link_href))
            self._link_href = None
            self._link_parts = []
        elif tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._noise_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
            return
        if self._link_href is not None:
            self._link_parts.append(data)
        self._chunks.append(data)

    @property
    def title(self) -> str:
        return "".join(self._title_parts).strip()

    @property
    def text(self) -> str:
        raw = "".join(self._chunks)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n\s*\n+", "\n\n", raw)
        return raw.strip()


def _is_private_ip(ip: str) -> bool:
    """Reject addresses that must never be reachable by the web tool."""
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return any((
        address.is_private,
        address.is_loopback,
        address.is_link_local,
        address.is_reserved,
        address.is_multicast,
        address.is_unspecified,
    ))


def _is_safe_url(url: str) -> tuple[bool, str]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "Only http:// and https:// URLs are supported"
    if not parsed.hostname:
        return False, "URL is missing a host"

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"}:
        return False, "Requests to local hostnames are not permitted"

    try:
        infos = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except (socket.gaierror, OSError, ValueError):
        return False, f"Could not resolve host '{hostname}'"

    addresses = {info[4][0] for info in infos}
    if not addresses:
        return False, f"Could not resolve host '{hostname}'"
    if any(_is_private_ip(ip) for ip in addresses):
        return False, "Requests to private/internal network ranges are not permitted"
    return True, ""


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Revalidate every redirect destination instead of trusting urllib blindly."""

    max_redirections = _MAX_REDIRECTS

    def _redirect_request(self, req: urllib.request.Request, fp, code: int, msg: str, headers, newurl: str):
        safe, reason = _is_safe_url(newurl)
        if not safe:
            raise urllib.error.URLError(f"Redirect blocked: {reason}")
        return super()._redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SafeRedirectHandler())


def _fetch(url: str) -> dict[str, Any]:
    safe, reason = _is_safe_url(url)
    if not safe:
        return {"status": "blocked", "message": reason, "url": url}

    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with _opener.open(request, timeout=_TIMEOUT) as resp:
            ct = resp.headers.get_content_type() or ""
            if ct and "html" not in ct and "xhtml" not in ct:
                return {"status": "unsupported_content_type", "message": f"Page returned Content-Type '{ct}' — not HTML", "url": url}
            raw = resp.read(_MAX_BYTES + 1)
            over_limit = len(raw) > _MAX_BYTES
            raw = raw[:_MAX_BYTES]
            charset = resp.headers.get_content_charset() or "utf-8"
            html = raw.decode(charset, errors="replace")
            final_url = resp.geturl()
            final_safe, final_reason = _is_safe_url(final_url)
            if not final_safe:
                return {"status": "blocked", "message": final_reason, "url": final_url}
    except urllib.error.HTTPError as exc:
        return {"status": "http_error", "message": f"HTTP {exc.code}: {exc.reason}", "url": url}
    except urllib.error.URLError as exc:
        return {"status": "connection_error", "message": str(exc.reason), "url": url}
    except (socket.timeout, TimeoutError):
        return {"status": "timeout", "message": f"Request timed out after {_TIMEOUT}s", "url": url}
    except OSError as exc:
        return {"status": "error", "message": str(exc), "url": url}

    extractor = _TextExtractor()
    try:
        extractor.feed(html)
    except Exception as exc:
        return {"status": "parse_error", "message": str(exc), "url": url}

    text = extractor.text
    text_truncated = len(text) > _MAX_TEXT
    text = text[:_MAX_TEXT]
    links = [{"text": t, "url": urljoin(final_url, href)} for t, href in extractor.links[:_MAX_LINKS]]

    return {
        "status": "ok",
        "url": final_url,
        "title": extractor.title,
        "text": text,
        "links": links,
        "truncated": bool(text_truncated or over_limit),
        "note": "This page may use JavaScript for rendering. Some content may not be visible in the static fetch." if not text.strip() else None,
    }


def browse_url(url: str) -> dict[str, Any]:
    """Fetch a public web page and return its readable text, title, and links."""
    if not url or not url.strip():
        return {"status": "error", "message": "'url' is required"}
    return _fetch(url.strip())
