"""
tools/browser.py
=================
Fetch a web page and return its readable text content to the JARVIS agent.

This replaces the previous ``not_implemented`` stub with a real, stdlib-only
implementation. It is intentionally narrow in scope:

  - Fetches a URL over http/https with a sane timeout
  - Strips <script>, <style>, <nav>, <header>, <footer> noise
  - Returns the page title, readable text, and outbound links
  - Truncates output so a single page cannot blow the model's context window
  - Guards against SSRF (server-side request forgery): the model cannot use
    this tool to reach JARVIS's own local services (Ollama, OmniRoute, etc.)

Out of scope for this version (documented, not silently missing):
  - JavaScript rendering (no Playwright/headless browser dependency)
  - Multi-page crawling or link following
  - Cookie/session/authentication handling

No external dependencies. Uses only ``urllib`` and ``html.parser`` from the
Python standard library.

Tool registration (tools/registry.py):
    ToolSpec("browse_url", ..., browse_url, frozenset({Permission.NETWORK}), risk_level="low")

Tool call the model emits:
    TOOL_CALL:browse_url:{"url": "https://example.com/article"}
"""

from __future__ import annotations

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

_USER_AGENT = (
    "Mozilla/5.0 (compatible; JARVIS-personal-agent/1.0; "
    "+https://github.com/Muneer148/JARVIS)"
)

_NOISE_TAGS = frozenset({"script", "style", "nav", "header", "footer", "noscript", "svg", "aside"})
_BLOCK_TAGS = frozenset({
    "p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "tr", "blockquote", "section", "article", "pre", "code",
})


class _TextExtractor(HTMLParser):
    """Minimal readable-text extractor. No external deps, fully inspectable."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._title_parts: list[str] = []
        self._in_title = False
        self._noise_depth = 0
        self._chunks: list[str] = []
        self._link_href: str | None = None
        self._link_parts: list[str] = []
        self.links: list[tuple[str, str]] = []  # (link_text, href)

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


# ------------------------------------------------------------------
# SSRF guard — prevent the model from reaching JARVIS's own local
# services (Ollama on 11434, OmniRoute on 20128, etc.)
# ------------------------------------------------------------------

_LOCAL_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "::1"})


def _is_safe_url(url: str) -> tuple[bool, str]:
    """Return (safe, reason). Reject local/internal targets."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "Only http:// and https:// URLs are supported"
    if not parsed.netloc:
        return False, "URL is missing a host"

    hostname = (parsed.hostname or "").lower()
    if hostname in _LOCAL_HOSTNAMES:
        return False, "Requests to local/loopback addresses are not permitted"

    try:
        resolved = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror:
        return False, f"Could not resolve host '{hostname}'"

    for ip in resolved:
        if _is_private_ip(ip):
            return False, "Requests to private/internal network ranges are not permitted"

    return True, ""


def _is_private_ip(ip: str) -> bool:
    if ip.startswith(("127.", "10.", "169.254.")):
        return True
    if ip in ("::1", "0.0.0.0"):
        return True
    if ip.startswith("192.168."):
        return True
    if ip.startswith("172."):
        try:
            second = int(ip.split(".")[1])
            if 16 <= second <= 31:
                return True
        except (IndexError, ValueError):
            pass
    return False


# ------------------------------------------------------------------
# Core fetch
# ------------------------------------------------------------------


def _fetch(url: str) -> dict[str, Any]:
    """Internal fetch — returns a result dict, never raises on expected failures."""
    safe, reason = _is_safe_url(url)
    if not safe:
        return {"status": "blocked", "message": reason, "url": url}

    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as resp:
            ct = resp.headers.get_content_type() or ""
            if ct and "html" not in ct and "xhtml" not in ct:
                return {
                    "status": "unsupported_content_type",
                    "message": f"Page returned Content-Type '{ct}' — not HTML",
                    "url": url,
                }
            raw = resp.read(_MAX_BYTES + 1)
            over_limit = len(raw) > _MAX_BYTES
            raw = raw[:_MAX_BYTES]
            charset = resp.headers.get_content_charset() or "utf-8"
            html = raw.decode(charset, errors="replace")
            final_url = resp.geturl()
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

    links = [
        {"text": t, "url": urljoin(final_url, href)}
        for t, href in extractor.links[:_MAX_LINKS]
    ]

    return {
        "status": "ok",
        "url": final_url,
        "title": extractor.title,
        "text": text,
        "links": links,
        "truncated": bool(text_truncated or over_limit),
        "note": (
            "This page may use JavaScript for rendering. "
            "Some content may not be visible in the static fetch."
        ) if not extractor.text.strip() else None,
    }


# ------------------------------------------------------------------
# Tool handler — signature matches TOOL_CALL:{\"url\": \"...\"} payload
# ------------------------------------------------------------------


def browse_url(url: str) -> dict[str, Any]:
    """Fetch a web page and return its readable text, title, and links.

    Only public http/https URLs are supported. Local services are blocked.

    Args:
        url: The full URL to fetch (e.g. https://example.com/article).
    """
    if not url or not url.strip():
        return {"status": "error", "message": "'url' is required"}
    return _fetch(url.strip())
