"""Tests that verify all include() references in templates point to existing files."""

import re

import pytest

from tests.utils import PROJECT_ROOT, TEMPLATES_DIR, get_all_templates, load_yaml_file

INCLUDE_PATTERN = re.compile(r"""include\(\s*['"]([^'"]+)['"]\s*\)""")


def _include_pairs():
    pairs = []
    for template_path in get_all_templates():
        data = load_yaml_file(template_path.relative_to(PROJECT_ROOT))
        content = data.get("content", "") or ""
        for match in INCLUDE_PATTERN.finditer(content):
            included = match.group(1)
            rel_source = str(template_path.relative_to(TEMPLATES_DIR))
            pairs.append(pytest.param(rel_source, included, id=f"{rel_source}::{included}"))
    return pairs


INCLUDE_PAIRS = _include_pairs()


@pytest.mark.parametrize("source_template,included_path", INCLUDE_PAIRS)
def test_include_reference_resolves(source_template, included_path):
    """Test that each include() reference in a template points to an existing file."""
    # Mirror YamlContentLoader: auto-append .yaml if missing
    resolved = included_path if included_path.endswith(".yaml") else included_path + ".yaml"
    full_path = TEMPLATES_DIR / resolved
    assert full_path.exists(), (
        f"Template '{source_template}' references '{included_path}' "
        f"but '{resolved}' does not exist in templates directory"
    )
