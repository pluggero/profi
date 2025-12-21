"""Snapshot tests for template outputs to detect regressions."""

import os
from pathlib import Path

import pytest

from profi.renderer import render_template
from tests.utils import get_all_templates


def get_test_config():
    """Create a consistent test configuration."""
    # Set predictable environment variables for testing
    os.environ["OP_ATTACKER_IP"] = "10.10.14.5"
    os.environ["OP_ATTACKER_INTERFACE"] = "tun0"
    os.environ["OP_SHELL_PORT"] = "4444"
    os.environ["OP_DELIVERY_INBOUND_PORT"] = "8085"
    os.environ["OP_DELIVERY_OUTBOUND_PORT"] = "8086"
    os.environ["OP_DELIVERY_PATH_LINUX"] = "/dev/shm"
    os.environ["OP_DELIVERY_PATH_WINDOWS"] = "C:\\Windows\\Temp"
    os.environ["OP_PROXY_PORT"] = "8087"
    os.environ["OP_WEBDAV_PORT"] = "80"
    os.environ["OP_TOOLS_DIR"] = "/home/user/.local/share/profi/tools"
    os.environ["OP_TEMPLATES_DIR"] = "/home/user/.local/share/profi/templates"

    return {}


class TestTemplateOutputs:
    """Test that all templates render without errors."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Setup test environment before each test."""
        # Store original env vars
        self.original_env = dict(os.environ)
        get_test_config()
        yield
        # Restore original env vars
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_all_templates_render_successfully(self):
        """Test that all templates can be rendered without errors."""
        templates_dir = Path(__file__).parent.parent / "src" / "profi" / "templates"
        config = get_test_config()

        errors = []
        success_count = 0

        for template_file in get_all_templates():
            # Get relative path from templates directory
            rel_path = template_file.relative_to(templates_dir)

            try:
                rendered, _ = render_template(str(rel_path), templates_dir, config, debug=False)

                # Basic sanity checks
                assert rendered is not None, f"Template {rel_path} returned None"
                assert isinstance(rendered, str), f"Template {rel_path} did not return string"

                success_count += 1

            except Exception as e:
                errors.append(f"{rel_path}: {type(e).__name__}: {str(e)}")

        # Report results
        if errors:
            error_msg = f"\n\nFailed to render {len(errors)} templates:\n"
            error_msg += "\n".join(f"  - {err}" for err in errors[:20])  # Show first 20
            if len(errors) > 20:
                error_msg += f"\n  ... and {len(errors) - 20} more"
            pytest.fail(error_msg)

        assert success_count > 0, "No templates were tested"

    def test_sample_templates_output(self):
        """Test specific templates and verify their output structure."""
        templates_dir = Path(__file__).parent.parent / "src" / "profi" / "templates"
        config = get_test_config()

        # Test a simple payload template
        test_cases = [
            {
                "template": "payloads/revshell-linux-busybox-nc.yaml",
                "expected_contains": ["busybox", "10.10.14.5", "4444"],
                "not_contains": ["{{", "}}"]  # No unrendered Jinja2
            },
        ]

        for test_case in test_cases:
            template_path = test_case["template"]

            try:
                rendered, _ = render_template(template_path, templates_dir, config, debug=False)

                # Check expected content
                for expected in test_case.get("expected_contains", []):
                    assert expected in rendered, f"Template {template_path} should contain '{expected}'"

                # Check forbidden content
                for forbidden in test_case.get("not_contains", []):
                    assert forbidden not in rendered, f"Template {template_path} should not contain '{forbidden}'"

            except FileNotFoundError:
                pytest.skip(f"Template {template_path} not found")

    def test_templates_with_includes(self):
        """Test that templates with includes work correctly."""
        templates_dir = Path(__file__).parent.parent / "src" / "profi" / "templates"
        config = get_test_config()

        # Find a template that uses includes (if it exists)
        include_templates = [
            "payloads/revshell-windows-powershell-oneliner-base64encoded.yaml",
        ]

        for template_path in include_templates:
            full_path = templates_dir / template_path

            if not full_path.exists():
                continue

            try:
                rendered, _ = render_template(template_path, templates_dir, config, debug=False)

                # Should not contain Jinja2 syntax
                assert "{{" not in rendered, f"Unrendered Jinja2 in {template_path}"
                assert "}}" not in rendered, f"Unrendered Jinja2 in {template_path}"
                assert "{%" not in rendered, f"Unrendered Jinja2 in {template_path}"
                assert "%}" not in rendered, f"Unrendered Jinja2 in {template_path}"

                # Should contain actual content
                assert len(rendered) > 10, f"Template {template_path} output too short"

            except Exception as e:
                pytest.fail(f"Failed to render {template_path}: {e}")

    def test_variable_substitution(self):
        """Test that variables are correctly substituted."""
        templates_dir = Path(__file__).parent.parent / "src" / "profi" / "templates"
        config = get_test_config()

        # Test a template we know has variables
        template_path = "payloads/revshell-linux-busybox-nc.yaml"
        full_path = templates_dir / template_path

        if not full_path.exists():
            pytest.skip(f"Template {template_path} not found")

        rendered, _ = render_template(template_path, templates_dir, config, debug=False)

        # Check that environment variable values appear in output
        assert "10.10.14.5" in rendered, "ATTACKER_IP should be substituted"
        assert "4444" in rendered, "SHELL_PORT should be substituted"
