"""Custom Jinja2 loader for YAML templates with content extraction."""

from pathlib import Path

import yaml
from jinja2 import BaseLoader, Environment, TemplateNotFound


class YamlContentLoader(BaseLoader):
    """
    Loads YAML templates and extracts only the 'content' field.

    This enables template composition without including metadata.
    When a template includes another template, only the content is rendered.
    """

    def __init__(self, templates_dir: Path):
        """Initialize with the base templates directory."""
        self.templates_dir = Path(templates_dir)

    def get_source(self, environment: Environment, template: str):
        """
        Load template and extract content field.

        Args:
            environment: Jinja2 environment instance
            template: Relative path to template (e.g., "payloads/example.yaml")

        Returns:
            Tuple of (source, filename, uptodate_function)

        Raises:
            TemplateNotFound: If template doesn't exist or can't be loaded
        """
        # Ensure .yaml extension
        if not template.endswith('.yaml'):
            template = f"{template}.yaml"

        path = self.templates_dir / template

        if not path.exists():
            raise TemplateNotFound(template)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            # Extract only content field
            source = data.get('content', '')

            # Cache invalidation based on modification time
            mtime = path.stat().st_mtime

            def uptodate():
                try:
                    return path.stat().st_mtime == mtime
                except OSError:
                    return False

            return source, str(path), uptodate

        except (yaml.YAMLError, OSError) as e:
            raise TemplateNotFound(f"Error loading {template}: {e}")
