import os
import sys

from .utils import get_available_tags

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from profi import profi


def test_tag_in_config():
    """Ensure the default config includes available tags."""
    errors = set()
    available_tags = get_available_tags()

    found_tags = set(profi.DEFAULT_CONFIG["colors"].keys())

    missing = available_tags - found_tags
    extra = found_tags - available_tags

    if missing:
        errors.add(f"Tag missing in default config: {missing}")
    if extra:
        errors.add(f"Unknown tag found in default config: {extra}")

    assert not errors, f"Default config tag issues: {errors}"
