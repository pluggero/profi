import os
import subprocess
import yaml
from pathlib import Path
import importlib.resources
import click

def load_config():
    # Check if the config file exists and read it, otherwise create it with default values
    config_file_path = Path("~/.config/profi/config.yaml").expanduser()

    if not config_file_path.exists():
        # Define the configuration data as a dictionary
        config_data = {
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

        # Ensure the directory exists
        config_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the configuration data to the YAML file
        with open(config_file_path, "w") as file:
            yaml.dump(
                config_data,
                file,
                default_flow_style=False,
                default_style='"',
                sort_keys=False,
            )

    # Load the configuration from the YAML file
    with open(config_file_path, "r") as file:
        config = yaml.safe_load(file)

    # Set environment variables from the loaded configuration with 'OP_' prefix and uppercase names
    for key, value in config["settings"].items():
        if value:
            os.environ[f"OP_{key.upper()}"] = str(value)

    return config

def get_available_templates(template_dir):
    # Change directory to templates
    templates_dir = os.path.expanduser(template_dir)
    os.chdir(templates_dir)

    # Find files, excluding certain paths
    find_command = "find . -type f -not -path './helper_scripts/*' -not -path './source_code/*' -not -path './variables/*'"
    templates = []
    try:
        find_result = subprocess.check_output(find_command, shell=True, env=os.environ).splitlines()
        templates = [line.decode('utf-8') for line in find_result]
    except subprocess.CalledProcessError:
        exit()

    return templates

@click.command()
@click.option("-t", "--template", help="The template to be executed, skipping rofi", type=click.Choice(get_available_templates(os.path.expanduser(load_config()["templates_dir"]))))
def main(template):
    config = load_config()

    tools_dir = os.path.expanduser(config["tools_dir"])
    os.environ["OP_TOOLS_DIR"] = tools_dir

    # Change directory to templates
    templates_dir = os.path.expanduser(config["templates_dir"])
    os.chdir(templates_dir)

    selected_file = ""

    if template:

        selected_file = template

    else:

        templates = get_available_templates(templates_dir)

        combined_templates = "\n".join(templates)

        file_selection_command = f"printf '{combined_templates}' | rofi -dmenu -i -p 'Template'"

        try:
            selected_file = (
                subprocess.check_output(file_selection_command, shell=True, env=os.environ)
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError:
            exit()

    # Process the selected file
    if selected_file:
        esh_command = f"esh '{selected_file}'"
        perl_command = "perl -pe 'chomp if eof'"
        copy_command = config["copy_command"]

        # Pipe the output from esh to perl, then to the copy command
        final_command = f"{esh_command} | {perl_command} | {copy_command}"
        subprocess.run(final_command, shell=True, env=os.environ)
