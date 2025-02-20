import importlib.resources
import os
import subprocess
import sys
from pathlib import Path

import click
import yaml

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

    return config


def get_available_templates(template_dir: str) -> list[str]:
    """
    Recursively collect template files from the provided directory,
    excluding certain subdirectories.
    """
    templates = []
    root = Path(template_dir).expanduser()

    if not root.is_dir():
        return templates

    for f in root.rglob("*"):
        if f.is_file():
            # Exclude certain folders
            parts = set(f.parts)
            if not {"helper_scripts", "source_code", "variables"}.intersection(parts):
                # Store the file path relative to the templates root
                templates.append(str(f.relative_to(root)))

    return templates


@click.command()
@click.option(
    "-t",
    "--template",
    help="The template to be executed, skipping rofi",
    type=click.Choice(
        get_available_templates(os.path.expanduser(load_config()["templates_dir"]))
    ),
)
def main(template: str):
    """
    Command-line entry point for profi.
    Uses a pre-selected template if provided, otherwise prompts via rofi.
    """
    config = load_config()

    tools_dir = os.path.expanduser(config["tools_dir"])
    os.environ["OP_TOOLS_DIR"] = tools_dir

    # Change directory to templates
    templates_dir = os.path.expanduser(config["templates_dir"])
    available_templates = get_available_templates(templates_dir)

    if template:
        selected_file = template
    else:
        # Show rofi menu
        combined_templates = "\n".join(available_templates)
        file_selection_command = ["rofi", "-dmenu", "-i", "-p", "Template"]

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
            selected_file = rofi_proc.stdout.strip()
        except FileNotFoundError:
            click.echo("Error: rofi is not installed or not found in PATH.", err=True)
            sys.exit(1)

    if not selected_file:
        # User didn't pick anything
        sys.exit(0)

    # Build up the pipeline: esh -> perl -> copy_command
    # We can do each step separately to avoid shell piping
    copy_command = config["copy_command"].split()
    try:
        # 1) Run esh
        esh_result = subprocess.run(
            ["esh", selected_file],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(templates_dir),
        )

        # 2) Run perl
        perl_result = subprocess.run(
            ["perl", "-pe", "chomp if eof"],
            input=esh_result.stdout,
            capture_output=True,
            text=True,
            check=True,
        )

        # 3) Run copy command
        subprocess.run(copy_command, input=perl_result.stdout, text=True, check=True)
    except FileNotFoundError as fnf:
        click.echo(f"Error: required command not found -> {fnf}", err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as cpe:
        click.echo(f"Error running command: {cpe}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
