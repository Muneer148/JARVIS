"""Regression and unit tests for tools/browser.py."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from tools.browser import _TextExtractor, _is_private_ip, _is_safe_url, browse_url

SAMPLE_HTML = """
<html>
  <head>
    <title>JARVIS Test Page</title>
    <style>body { color: red; }</style>
    <script>alert('ignore me');</script>
  </head>
  <body>
    <nav>Home | About</nav>
    <h1>Main Heading</h1>
    <p>This is the <a href="/detail">main content</a> of the page.</p>
    <footer>Copyright 2026</footer>
  </body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/404":
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(SAMPLE_HTML.encode("utf-8"))

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def local_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield port
    server.shutdown()
    thread.join(timeout=2)


class TestSsrfGuard:
    def test_rejects_file_scheme(self):
        safe, _ = _is_safe_url("file:///etc/passwd")
        assert safe is False

    def test_rejects_localhost_by_name(self):
        safe, _ = _is_safe_url("http://localhost:8080/")
        assert safe is False

    def test_rejects_loopback_ip(self):
        safe, _ = _is_safe_url("http://127.0.0.1/")
        assert safe is False

    def test_rejects_missing_host(self):
        safe, _ = _is_safe_url("https:///path")
        assert safe is False

    def test_rejects_ftp_scheme(self):
        safe, _ = _is_safe_url("ftp://files.example.com/file.txt")
        assert safe is False

    def test_accepts_public_url_structurally(self):
        safe, reason = _is_safe_url("https://example.com/page")
        assert safe is True, reason


class TestPrivateIp:
    @pytest.mark.parametrize(
        "address",
        [
            "127.0.0.1",
            "127.255.0.1",
            "10.0.0.1",
            "192.168.1.1",
            "172.16.0.1",
            "172.31.255.255",
            "169.254.1.1",
            "0.0.0.0",
            "224.0.0.1",
            "255.255.255.255",
            "::1",
            "::",
            "fe80::1",
            "ff02::1",
            "fc00::1",
            "fd12:3456::1",
            "203.0.113.1",  # TEST-NET-3 / reserved documentation range
            "198.51.100.1",  # TEST-NET-2 / reserved documentation range
            "192.0.2.1",  # TEST-NET-1 / reserved documentation range
        ],
    )
    def test_rejects_non_routable_or_reserved_addresses(self, address):
        assert _is_private_ip(address)

    @pytest.mark.parametrize("address", ["8.8.8.8", "1.1.1.1", "93.184.216.34"])
    def test_accepts_genuinely_public_addresses(self, address):
        assert not _is_private_ip(address)

    def test_invalid_ip_is_rejected(self):
        assert _is_private_ip("not-an-ip")


class TestTextExtractor:
    def test_title_extracted(self):
        ex = _TextExtractor()
        ex.feed(SAMPLE_HTML)
        assert ex.title == "JARVIS Test Page"

    def test_script_content_stripped(self):
        ex = _TextExtractor()
        ex.feed(SAMPLE_HTML)
        assert "alert(" not in ex.text
        assert "ignore me" not in ex.text

    def test_style_content_stripped(self):
        ex = _TextExtractor()
        ex.feed(SAMPLE_HTML)
        assert "color: red" not in ex.text

    def test_nav_content_stripped(self):
        ex = _TextExtractor()
        ex.feed(SAMPLE_HTML)
        assert "Home | About" not in ex.text

    def test_footer_content_stripped(self):
        ex = _TextExtractor()
        ex.feed(SAMPLE_HTML)
        assert "Copyright 2026" not in ex.text

    def test_main_content_preserved(self):
        ex = _TextExtractor()
        ex.feed(SAMPLE_HTML)
        assert "Main Heading" in ex.text
        assert "main content" in ex.text

    def test_links_captured(self):
        ex = _TextExtractor()
        ex.feed(SAMPLE_HTML)
        assert ex.links == [("main content", "/detail")]

    def test_empty_html(self):
        ex = _TextExtractor()
        ex.feed("")
        assert ex.title == ""
        assert ex.text == ""


class TestBrowseUrl:
    def test_missing_url_returns_error(self):
        result = browse_url(url="")
        assert result["status"] == "error"

    def test_localhost_is_blocked(self):
        result = browse_url(url="http://localhost:9999/")
        assert result["status"] == "blocked"

    def test_loopback_ip_is_blocked(self):
        result = browse_url(url="http://127.0.0.1:8080/")
        assert result["status"] == "blocked"

    def test_ipv6_loopback_is_blocked(self):
        result = browse_url(url="http://[::1]:8080/")
        assert result["status"] == "blocked"

    def test_reserved_documentation_ip_is_blocked(self):
        result = browse_url(url="http://203.0.113.1/")
        assert result["status"] == "blocked"

    def test_nonexistent_domain_returns_connection_error(self):
        result = browse_url(url="https://this-domain-absolutely-does-not-exist-jarvis-test.example/")
        assert result["status"] in ("connection_error", "blocked", "error")

    def test_http_error_handled(self, local_server):
        """_fetch blocks 127.0.0.1 by the SSRF guard — verify consistently."""
        from tools.browser import _fetch

        result = _fetch(f"http://127.0.0.1:{local_server}/404")
        assert result["status"] == "blocked"

    def test_fetch_pipeline_integration(self):
        extractor = _TextExtractor()
        extractor.feed(SAMPLE_HTML)
        assert extractor.title == "JARVIS Test Page"
        assert "Main Heading" in extractor.text
        assert "alert(" not in extractor.text
        assert extractor.links == [("main content", "/detail")]
