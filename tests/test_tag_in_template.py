from .utils import get_all_templates, get_available_tags, load_yaml_file


def test_tag_in_template():
    """Check that templates contain available tags."""
    errors = set()

    for filepath in get_all_templates():

        try:
            content = load_yaml_file(filepath)
        except Exception:
            continue  # Error already handled in another test
        if not isinstance(content, dict):
            continue  # Error already handled in another test

        metadata = content.get("metadata", {})
        found_tags = metadata.get("tags")
        if not found_tags:
            errors.add(f"No tag in template: {filepath.name}")

        available_tags = get_available_tags()

        extra = set(found_tags) - available_tags

        if extra:
            errors.add(f"Unknown tag in template: {filepath.name}: {extra}")

    assert not errors, f"Template tag issues: {errors}"
