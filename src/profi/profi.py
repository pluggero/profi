import os
import subprocess
import argparse
import yaml
from pathlib import Path
import importlib.resources

def main():
    # Setup argparse
    parser = argparse.ArgumentParser(description="Script Description")
    # Add arguments as needed here
    # e.g., parser.add_argument('-f', '--flag', action='store_true', help='An example flag')
    args = parser.parse_args()

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

    tools_dir = os.path.expanduser(config["tools_dir"])
    os.environ["OP_TOOLS_DIR"] = tools_dir

    # Change directory to templates
    templates_dir = os.path.expanduser(config["templates_dir"])
    os.chdir(templates_dir)

    # Find files, excluding certain paths, and select one using rofi with environment variables
    find_command = "find . -type f -not -path './helper_scripts/*' -not -path './source_code/*' -not -path './variables/*'"
    file_selection_command = f"{find_command} | rofi -dmenu -i -p 'Template'"

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
