from .utils import get_all_templates, load_yaml_file

REQUIRED_METADATA_FIELDS = ["filename", "tags", "created", "author"]
REQUIRED_TOP_LEVEL_FIELDS = ["metadata", "content"]


def has_keys(d: dict, keys: list[str]) -> list[str]:
    """Returns list of missing keys."""
    return [key for key in keys if key not in d]


def test_template_structure():
    """Ensure each template has required top-level and metadata keys."""
    errors = set()

    for filepath in get_all_templates():

        try:
            content = load_yaml_file(filepath)
        except Exception:
            continue  # Error already handled in another test
        if not isinstance(content, dict):
            continue  # Error already handled in another test

        missing_top_fields = has_keys(content, REQUIRED_TOP_LEVEL_FIELDS)
        if missing_top_fields:
            errors.add(filepath.name)

        metadata = content.get("metadata", {})
        missing_metadata_fields = has_keys(metadata, REQUIRED_METADATA_FIELDS)
        if missing_metadata_fields:
            errors.add(filepath.name)

    assert not errors, f"Templates that miss required yaml parameters: {errors}"
