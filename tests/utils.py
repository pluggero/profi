from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "src" / "profi" / "templates"
AVAILABLE_TAGS = {
    "api",
    "cracking",
    "domain",
    "linux",
    "mobile",
    "privesc",
    "proxy",
    "shell",
    "system",
    "utils",
    "web",
    "windows",
    "wordlist",
}


def get_available_tags():
    """Return a set of available tags."""
    return AVAILABLE_TAGS


def get_all_templates():
    """Recursively return all template names under TEMPLATES_DIR, matching all YAML file extensions."""
    return [
        f
        for f in TEMPLATES_DIR.rglob("*")
        if f.is_file() and f.suffix.lower() in {".yaml", ".yml"}
    ]


def get_relative_yaml_paths():
    """Returns file paths relative to PROJECT_ROOT."""
    return [f.relative_to(PROJECT_ROOT) for f in get_all_yaml_files()]


def load_yaml_file(path: Path) -> dict:
    """Load a YAML file given a Path relative to PROJECT_ROOT."""
    full_path = PROJECT_ROOT / path

    if not full_path.exists():
        raise FileNotFoundError(f"YAML file not found: {full_path}")

    with open(full_path, "r") as f:
        try:
            content = yaml.safe_load(f)
            if content is None:
                raise ValueError(f"YAML file {full_path} is empty or invalid")
            return content
        except yaml.YAMLError as e:
            raise ValueError(f"YAML file {full_path} failed to parse: {e}")
