from .utils import get_all_templates, load_yaml_file


def test_malformed_yaml():
    """Ensure each template has valid yaml."""
    errors = set()

    for filepath in get_all_templates():

        try:
            content = load_yaml_file(filepath)
            if content is None:
                errors.add(filepath.name)
        except Exception:
            errors.add(filepath.name)
        if not isinstance(content, dict):
            errors.add(filepath.name)

    assert not errors, f"Templates that have malformed yaml: {errors}"
