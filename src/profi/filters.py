"""Custom Jinja2 filters for payload encoding and transformation."""

import base64
import re
import urllib.parse


def url_encode(data: str) -> str:
    """URL encode for web requests. Example: "hello world" -> "hello%20world"."""
    return urllib.parse.quote(data, safe='')


def base64_encode(data: str) -> str:
    """Standard base64 encoding (UTF-8). Example: "hello" -> "aGVsbG8="."""
    return base64.b64encode(data.encode()).decode()


def base64_pwsh(data: str) -> str:
    """
    PowerShell -EncodedCommand compatible base64 encoding.

    Encodes as UTF-16 LE then base64, as required by PowerShell.
    Automatically removes BOM characters from editors like PowerShell ISE.
    """
    # Remove BOM characters
    bom_pattern = re.compile(u'(\xef|\xbb|\xbf)')
    cleaned = bom_pattern.sub("", data)

    # Convert to UTF-16 LE (insert null byte after each character)
    utf16_le = "".join(char + "\x00" for char in cleaned)

    # Base64 encode
    encoded = base64.b64encode(utf16_le.encode())
    return encoded.decode("utf-8")


def hex_encode(data: str) -> str:
    """Hexadecimal encoding. Example: "hello" -> "68656c6c6f"."""
    return ''.join(format(ord(c), '02x') for c in data)
