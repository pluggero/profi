from .utils import get_all_templates, load_yaml_file


def test_authors_is_list():
    """Ensure each template's metadata.authors field is a list."""
    errors = {}

    for filepath in get_all_templates():

        try:
            content = load_yaml_file(filepath)
        except Exception:
            continue  # Error already handled in another test
        if not isinstance(content, dict):
            continue  # Error already handled in another test

        metadata = content.get("metadata", {})
        authors = metadata.get("authors")

        # Check if authors field exists and is a list
        if authors is None or (authors is not None and not isinstance(authors, list)):
            errors[filepath.name] = f"authors has type {type(authors).__name__}, expected list"

    assert not errors, f"Templates with incorrect authors type: {errors}"
