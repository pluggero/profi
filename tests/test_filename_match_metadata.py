from .utils import get_all_templates, load_yaml_file


def test_filename_match_metadata():
    """Check that metadata.filename matches the file's name."""
    errors = set()

    for filepath in get_all_templates():
        expected_filename = filepath.name

        try:
            content = load_yaml_file(filepath)
        except Exception:
            continue  # Error already handled in another test
        if not isinstance(content, dict):
            continue  # Error already handled in another test

        metadata = content.get("metadata", {})
        actual_filename = metadata.get("filename")
        if not actual_filename:
            errors.add(filepath.name)

        if actual_filename != expected_filename:
            errors.add(filepath.name)

    assert not errors, f"Templates with mismatching metadata.filename: {errors}"
