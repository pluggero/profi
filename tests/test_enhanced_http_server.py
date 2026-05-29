"""Tests for the startEnhancedHttpServer helper script, including Range support."""

import importlib.util
import io
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

HELPER_PATH = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "profi"
    / "templates"
    / "helper_scripts"
    / "startEnhancedHttpServer.py"
)


def _load_server_module():
    """Load the helper script as a module (it lives outside any Python package)."""
    spec = importlib.util.spec_from_file_location("startEnhancedHttpServer", HELPER_PATH)
    assert spec and spec.loader, f"Cannot load module from {HELPER_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


server_mod = _load_server_module()


class TestParseByteRange:
    """Test parse_byte_range covers the spec'd inputs and rejects bad ones."""

    def test_full_range(self):
        assert server_mod.parse_byte_range("bytes=0-99") == (0, 99)

    def test_open_ended_range(self):
        assert server_mod.parse_byte_range("bytes=100-") == (100, None)

    def test_zero_zero(self):
        assert server_mod.parse_byte_range("bytes=0-0") == (0, 0)

    def test_empty_string_returns_nones(self):
        assert server_mod.parse_byte_range("") == (None, None)
        assert server_mod.parse_byte_range("   ") == (None, None)

    def test_inverted_range_raises(self):
        with pytest.raises(ValueError):
            server_mod.parse_byte_range("bytes=200-100")

    def test_wrong_unit_raises(self):
        with pytest.raises(ValueError):
            server_mod.parse_byte_range("lines=0-9")

    def test_garbage_raises(self):
        with pytest.raises(ValueError):
            server_mod.parse_byte_range("bytes=abc-def")

    def test_multi_range_unsupported(self):
        # The handler intentionally only supports a single range.
        with pytest.raises(ValueError):
            server_mod.parse_byte_range("bytes=0-10,20-30")


class TestCopyByteRange:
    """Test copy_byte_range writes the requested inclusive slice."""

    def test_copies_full_stream_when_no_bounds(self):
        src = io.BytesIO(b"abcdef")
        dst = io.BytesIO()
        server_mod.copy_byte_range(src, dst)
        assert dst.getvalue() == b"abcdef"

    def test_copies_inclusive_slice(self):
        src = io.BytesIO(b"abcdefghij")
        dst = io.BytesIO()
        server_mod.copy_byte_range(src, dst, start=2, stop=5)
        assert dst.getvalue() == b"cdef"

    def test_copies_from_start_to_end_when_stop_none(self):
        src = io.BytesIO(b"abcdefghij")
        dst = io.BytesIO()
        server_mod.copy_byte_range(src, dst, start=7)
        assert dst.getvalue() == b"hij"

    def test_respects_bufsize(self):
        src = io.BytesIO(b"abcdefghij")
        dst = io.BytesIO()
        server_mod.copy_byte_range(src, dst, start=0, stop=4, bufsize=2)
        assert dst.getvalue() == b"abcde"


@pytest.fixture
def make_server(tmp_path):
    """Factory fixture: start EnhancedRequestHandler on a background thread.

    Usage:
        base_url = make_server()                       # defaults
        base_url = make_server(allow_listing=True)     # with options
    """
    started = []

    def _start(allow_listing=False, show_headers=False):
        Handler = server_mod.EnhancedRequestHandler
        Handler.show_headers = show_headers
        Handler.allow_listing = allow_listing

        root = str(tmp_path)

        class _PinnedHandler(Handler):
            def translate_path(self, path):
                # Reuse SimpleHTTPRequestHandler's logic but anchored at tmp_path.
                import os
                import posixpath
                import urllib.parse

                path = path.split("?", 1)[0].split("#", 1)[0]
                trailing_slash = path.rstrip().endswith("/")
                try:
                    path = urllib.parse.unquote(path, errors="surrogatepass")
                except UnicodeDecodeError:
                    path = urllib.parse.unquote(path)
                path = posixpath.normpath(path)
                words = [w for w in path.split("/") if w and w not in (os.curdir, os.pardir)]
                translated = root
                for word in words:
                    translated = os.path.join(translated, word)
                if trailing_slash:
                    translated += "/"
                return translated

        httpd = HTTPServer(("127.0.0.1", 0), _PinnedHandler)  # type: ignore[arg-type]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        started.append((httpd, thread))
        return f"http://127.0.0.1:{httpd.server_address[1]}"

    yield _start

    for httpd, thread in started:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


@pytest.fixture
def http_server(make_server, tmp_path):
    """Default-options server, returned as (base_url, tmp_path)."""
    return make_server(), tmp_path


def _get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


class TestEnhancedRequestHandler:
    """Integration tests: real HTTPServer + EnhancedRequestHandler over loopback."""

    def test_full_get_returns_200(self, http_server):
        base, root = http_server
        (root / "hello.txt").write_bytes(b"Hello, world!")

        status, headers, body = _get(f"{base}/hello.txt")
        assert status == 200
        assert body == b"Hello, world!"
        assert headers.get("Accept-Ranges") == "bytes"

    def test_range_returns_206_with_slice(self, http_server):
        base, root = http_server
        payload = b"0123456789abcdef"
        (root / "data.bin").write_bytes(payload)

        status, headers, body = _get(f"{base}/data.bin", {"Range": "bytes=4-9"})
        assert status == 206
        assert body == payload[4:10]
        assert headers.get("Content-Range") == f"bytes 4-9/{len(payload)}"
        assert headers.get("Content-Length") == str(len(body))
        assert headers.get("Accept-Ranges") == "bytes"

    def test_open_ended_range_returns_tail(self, http_server):
        base, root = http_server
        payload = b"0123456789"
        (root / "data.bin").write_bytes(payload)

        status, headers, body = _get(f"{base}/data.bin", {"Range": "bytes=7-"})
        assert status == 206
        assert body == b"789"
        assert headers.get("Content-Range") == "bytes 7-9/10"

    def test_range_past_end_clamps_to_last_byte(self, http_server):
        base, root = http_server
        payload = b"0123456789"
        (root / "data.bin").write_bytes(payload)

        status, headers, body = _get(f"{base}/data.bin", {"Range": "bytes=5-999"})
        assert status == 206
        assert body == b"56789"
        assert headers.get("Content-Range") == "bytes 5-9/10"

    def test_range_start_beyond_eof_returns_416(self, http_server):
        base, root = http_server
        (root / "data.bin").write_bytes(b"0123456789")

        status, _, _ = _get(f"{base}/data.bin", {"Range": "bytes=100-200"})
        assert status == 416

    def test_invalid_range_returns_400(self, http_server):
        base, root = http_server
        (root / "data.bin").write_bytes(b"0123456789")

        status, _, _ = _get(f"{base}/data.bin", {"Range": "bytes=abc-"})
        assert status == 400

    def test_inverted_range_returns_400(self, http_server):
        base, root = http_server
        (root / "data.bin").write_bytes(b"0123456789")

        status, _, _ = _get(f"{base}/data.bin", {"Range": "bytes=9-3"})
        assert status == 400

    def test_accept_ranges_header_on_every_response(self, http_server):
        base, root = http_server
        (root / "a.txt").write_bytes(b"a")

        _, headers, _ = _get(f"{base}/a.txt")
        assert headers.get("Accept-Ranges") == "bytes"

    def test_directory_listing_forbidden_by_default(self, make_server):
        base = make_server(allow_listing=False)
        status, _, _ = _get(f"{base}/")
        assert status == 403

    def test_directory_listing_enabled(self, make_server, tmp_path):
        (tmp_path / "visible.txt").write_bytes(b"x")
        base = make_server(allow_listing=True)
        status, _, body = _get(f"{base}/")
        assert status == 200
        assert b"visible.txt" in body
