import importlib.resources
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import click
import yaml

from .renderer import render_template


@dataclass
class Metadata:
    filename: str
    tags: List[str]
    created: str
    author: str


DEFAULT_CONFIG = {
    "tools_dir": "~/.local/share/profi/tools",
    "templates_dir": str(importlib.resources.files("profi") / "templates"),
    "copy_command": "xclip -sel clip",
    "settings": {
        "attacker_interface": "tun0",
        "attacker_ip": "",
        "delivery_inbound_port": "8085",
        "delivery_outbound_port": "8086",
        "delivery_path_linux": "/dev/shm",
        "delivery_path_windows": "C:\\Windows\\Temp",
        "proxy_port": "8087",
        "shell_port": "4444",
        "webdav_port": "80",
    },
    "colors": {
        "web": "cyan",
        "api": "teal",
        "system": "orange",
        "shell": "red",
        "linux": "yellow",
        "windows": "lightblue",
        "domain": "blue",
        "mobile": "green",
        "cracking": "purple",
        "privesc": "pink",
        "proxy": "gray",
        "wordlist": "black",
        "utils": "tomato",
        "enum": "tan",
        "xss": "plum",
    },
}


def create_default_config(config_path: Path) -> None:
    """
    Create a default YAML config at the given path.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as file:
        yaml.dump(
            DEFAULT_CONFIG,
            file,
            default_flow_style=False,
            default_style='"',
            sort_keys=False,
        )


def load_config() -> dict:
    """
    Load the existing config. If it does not exist, create one with default values.
    Returns the loaded config as a dictionary.
    """

    # Check if the config file exists and read it, otherwise create it with default values
    config_file_path = Path("~/.config/profi/config.yaml").expanduser()
    if not config_file_path.exists():
        create_default_config(config_file_path)

    with config_file_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # Set environment variables from the loaded configuration with 'OP_' prefix and uppercase names
    for key, value in config["settings"].items():
        if value is not None:
            os.environ[f"OP_{key.upper()}"] = str(value)
    for key, value in config["colors"].items():
        if value is not None:
            os.environ[f"OP_COLOR_{key.upper()}"] = str(value)

    return config


def parse_metadata(file_path: Path) -> Metadata:
    """
    Reads the provided path, parses the metadata of the file into the Metadata class object
    and returns the object.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}  # Ensure data is not None

        metadata = data.get(
            "metadata", {}
        )  # Get metadata section, default to empty dict

        return Metadata(
            filename=metadata.get("filename", "unknown.yaml"),  # Default filename
            tags=metadata.get("tags", []),  # Default empty list if tags are missing
            created=metadata.get("created", "Unknown Date"),  # Default date string
            author=metadata.get("author", "Unknown"),  # Default author name
        )

    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error reading {file_path}: {e}")
        return Metadata(
            "unknown.yaml", [], "Unknown Date", "Unknown"
        )  # Fallback values


def parse_color_settings(yaml_file):
    """
    Parses the color settings from a YAML configuration file.
    """
    try:
        with open(yaml_file, "r") as file:
            config = yaml.safe_load(file)
            return config.get("colors", {})
    except FileNotFoundError:
        print(f"Error: The file {yaml_file} was not found.")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
    return {}


def get_op_color_env_vars():
    """Retrieve all OP_COLOR_* environment variables and return them as a dictionary."""
    return {
        key: value for key, value in os.environ.items() if key.startswith("OP_COLOR_")
    }


def check_tag_in_env(tags):
    """
    Check if any tag from the provided list has a matching OP_COLOR_* environment variable.

    :param tags: List of tags to check.
    :return: List of matching tags with their colors.
    """
    env_vars = get_op_color_env_vars()

    # Convert OP_COLOR_<TAG> to lowercase tag names
    env_tags = {
        key[9:].lower(): value for key, value in env_vars.items()
    }  # Remove 'OP_COLOR_' prefix

    # Find matches
    matches = {tag: env_tags[tag] for tag in tags if tag in env_tags}

    return matches


def build_tags(tags: list[str]) -> str:
    """
    Parses a list of given tags and combines them into a color-coded string.
    """
    tag_elements = []

    matching_tags = check_tag_in_env(tags)

    for tag in tags:
        color = matching_tags.get(tag)
        if color:
            tag_elements.append(f"<span color='{color}'>{tag}</span> ")
        else:
            tag_elements.append(f"<span>{tag}</span> ")

    tag_string = "".join(tag_elements)
    return f"<b>Tags:</b> {tag_string}"


def parse_payload(file_path: Path) -> str:
    """
    Reads the provided path, parses the payload of the file and returns it.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}  # Safely load YAML content

        # Extract the payload content
        return data.get("content", "")  # Default to an empty string if no content field

    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error reading {file_path}: {e}")
        return ""  # Return an empty string in case of an error


def get_available_templates(template_dir: str, clean: bool = False) -> list[str]:
    """
    Recursively collect template files from the provided directory,
    excluding certain subdirectories.
    The parameter 'clean' returns the list of templates without parsing the tags
    """
    templates = []
    root = Path(template_dir).expanduser()

    if not root.is_dir():
        return templates

    for f in root.rglob("*"):
        if f.is_file():
            # Exclude certain folders and files that are not YAML
            parts = set(f.parts)
            if not {"helper_scripts", "source_code", "variables"}.intersection(parts):
                # Only include YAML files
                if f.suffix in {".yaml"}:
                    # Store the file path relative to the templates root

                    if clean:
                        templates.append(str(f.relative_to(root)))
                    else:
                        metadata = parse_metadata(f)
                        tags = getattr(metadata, "tags")
                        tag_string = build_tags(tags)

                        file_name_without_ext = f.stem
                        templates.append(
                            str(f.relative_to(root).with_name(file_name_without_ext))
                            + f"\t({tag_string})"
                        )

    return templates


def print_debug_info(debug_info: dict):
    """
    Display debug information showing the rendering process.
    """
    click.echo("=" * 50)
    click.echo("DEBUG MODE")
    click.echo("=" * 50)
    click.echo(f"Template: {debug_info['template_path']}")
    click.echo()

    click.echo("Raw Template:")
    click.echo("-" * 20)
    click.echo(debug_info['raw_template'])
    click.echo()

    click.echo("Template Context (Variables):")
    click.echo("-" * 30)
    for key, value in sorted(debug_info['context'].items()):
        click.echo(f"{key}={value}")
    click.echo()

    click.echo("Rendered Output:")
    click.echo("-" * 20)
    click.echo(debug_info['rendered_output'])
    click.echo()

    click.echo("=" * 50)


@click.command()
@click.option(
    "-t",
    "--template",
    help="The template to be executed, skipping rofi",
    type=click.Choice(
        get_available_templates(
            os.path.expanduser(load_config()["templates_dir"]), True
        )
    ),
)
@click.option(
    "--debug",
    is_flag=True,
    help="Show debug information including esh processing steps",
)
def main(template: str, debug: bool):
    """
    Command-line entry point for profi.
    Uses a pre-selected template if provided, otherwise prompts via rofi.
    """
    config = load_config()

    tools_dir = os.path.expanduser(config["tools_dir"])
    os.environ["OP_TOOLS_DIR"] = tools_dir

    # Change directory to templates
    templates_dir = os.path.expanduser(config["templates_dir"])
    os.environ["OP_TEMPLATES_DIR"] = templates_dir
    available_templates = get_available_templates(templates_dir)

    if template:
        selected_file = template
    else:
        # Show rofi menu
        combined_templates = "\n".join(available_templates)
        file_selection_command = [
            "rofi",
            "-dmenu",
            "-i",
            "-p",
            "Template",
            "-markup-rows",
        ]

        try:
            # We provide the list of templates via stdin
            rofi_proc = subprocess.run(
                file_selection_command,
                input=combined_templates,
                text=True,
                capture_output=True,
                check=False,
            )
            if rofi_proc.returncode != 0:
                # This usually means user canceled
                sys.exit(0)
            # Remove the tags from the selected template and re-append the yaml file extension
            selected_file = rofi_proc.stdout.strip().split("\t", 1)[0] + ".yaml"
        except FileNotFoundError:
            click.echo("Error: rofi is not installed or not found in PATH.", err=True)
            sys.exit(1)

    if not selected_file:
        # User didn't pick anything
        sys.exit(0)

    # Render template using Jinja2
    copy_command = config["copy_command"].split()
    try:
        # Render the template
        rendered_output, debug_info = render_template(
            selected_file,
            Path(templates_dir),
            config,
            debug=debug
        )

        # Show debug information if requested
        if debug:
            print_debug_info(debug_info)
            click.echo("\n[Debug mode: Output not copied to clipboard]")
        else:
            # Copy to clipboard
            subprocess.run(copy_command, input=rendered_output, text=True, check=True)

    except FileNotFoundError as fnf:
        click.echo(f"Error: required command not found -> {fnf}", err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as cpe:
        click.echo(f"Error running command: {cpe}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error rendering template: {e}", err=True)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
