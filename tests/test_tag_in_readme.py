import re

from .utils import get_available_tags


def test_tag_in_readme():
    """Ensure the README includes available tags."""
    errors = set()
    available_tags = get_available_tags()

    with open("README.md", "r") as f:
        content = f.read()

    found_tags = set(re.findall(r"'>\s*(\w+)\s*<", content))

    missing = available_tags - found_tags
    extra = found_tags - available_tags

    if missing:
        errors.add(f"Tag missing in README: {missing}")
    if extra:
        errors.add(f"Unknown tag in README: {extra}")

    assert not errors, f"README tag issues: {errors}"
