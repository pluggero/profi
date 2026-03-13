#!/usr/bin/env python3
"""
Mythic C2 Payload Configuration Generator

This script generates Mythic payload configuration JSON from CLI parameters.
It can output to stdout (for piping) or save to a file for later use.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


def parse_commands(commands_str):
    """
    Parse commands string into a list.

    Args:
        commands_str: Either "all" or comma-separated list of commands

    Returns:
        List of command names, or special list for "all"
    """
    if commands_str.lower() == "all":
        # Return comprehensive Apollo command set
        return [
            "assembly_inject", "blockdlls", "cat", "cd", "cp", "dcsync",
            "download", "execute_assembly", "execute_coff", "execute_pe", "exit",
            "get_injection_techniques", "getprivs", "getsystem", "ifconfig", "inject",
            "inline_assembly", "jobkill", "jobs", "jump_psexec", "jump_wmi",
            "keylog_inject", "kill", "link", "listpipes", "load", "ls", "make_token",
            "mimikatz", "mkdir", "mv", "net_dclist", "net_localgroup",
            "net_localgroup_member", "net_shares", "netstat", "powerpick", "powershell",
            "powershell_import", "ppid", "printspoofer", "ps", "psinject", "pth", "pwd",
            "reg_query", "reg_write_value", "register_assembly", "register_coff",
            "register_file", "rev2self", "rm", "rpfwd", "run", "sc", "screenshot",
            "screenshot_inject", "set_injection_technique", "shell", "shinject", "sleep",
            "socks", "spawn", "spawnto_x64", "spawnto_x86", "steal_token",
            "ticket_cache_add", "ticket_cache_extract", "ticket_cache_list",
            "ticket_cache_purge", "ticket_store_add", "ticket_store_list",
            "ticket_store_purge", "unlink", "upload", "whoami", "wmiexecute"
        ]
    else:
        # Parse comma-separated list
        return [cmd.strip() for cmd in commands_str.split(',') if cmd.strip()]


def generate_config(args):
    """
    Generate Mythic payload configuration dictionary.

    Args:
        args: Parsed command-line arguments

    Returns:
        Dictionary containing Mythic payload configuration
    """
    # Calculate killdate (default: 1 year from now)
    if args.killdate:
        killdate = args.killdate
    else:
        future_date = datetime.now() + timedelta(days=365)
        killdate = future_date.strftime("%Y-%m-%d")

    # Parse commands
    commands = parse_commands(args.commands)

    # Build C2 profile parameters based on payload type
    c2_profile_params = {
        "AESPSK": {
            "dec_key": args.encryption_key if args.encryption_key else "aes256_hmac",
            "enc_key": args.encryption_key if args.encryption_key else "aes256_hmac",
            "value": "aes256_hmac"
        },
        "callback_host": args.callback_host,
        "callback_interval": args.callback_interval,
        "callback_jitter": args.callback_jitter,
        "callback_port": args.callback_port,
        "encrypted_exchange_check": True,
        "headers": {
            "User-Agent": args.user_agent
        },
        "killdate": killdate,
        "post_uri": "data",
        "proxy_host": "",
        "proxy_pass": "",
        "proxy_port": "",
        "proxy_user": ""
    }

    # Build parameters based on output type
    build_parameters = []

    if args.output_type.lower() == "shellcode":
        build_parameters = [
            {"name": "output_type", "value": "Shellcode"},
            {"name": "shellcode_format", "value": args.shellcode_format},
            {"name": "shellcode_bypass", "value": "Continue on fail"},
            {"name": "adjust_filename", "value": True},
            {"name": "debug", "value": False}
        ]
    elif args.output_type.lower() == "exe":
        build_parameters = [
            {"name": "output_type", "value": "WinExe"},
            {"name": "adjust_filename", "value": True},
            {"name": "debug", "value": False}
        ]
    elif args.output_type.lower() == "dll":
        build_parameters = [
            {"name": "output_type", "value": "WinDLL"},
            {"name": "adjust_filename", "value": True},
            {"name": "debug", "value": False}
        ]

    # Build the final configuration
    config = {
        "description": f"Created by profi at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "payload_type": args.payload_type,
        "c2_profiles": [
            {
                "c2_profile": "http",
                "c2_profile_is_p2p": False,
                "c2_profile_parameters": c2_profile_params
            }
        ],
        "build_parameters": build_parameters,
        "commands": commands,
        "selected_os": args.selected_os,
        "filename": args.filename if args.filename else f"{args.payload_type}-payload.bin",
        "wrapped_payload": ""
    }

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mythic C2 payload configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Apollo shellcode config and pipe to payload generator
  %(prog)s --payload-type apollo --callback-host 192.168.1.10 --callback-port 80 \\
    --output-type shellcode --commands all | mythicPayloadGenerator.py --stdin

  # Save config to file for later use
  %(prog)s --payload-type apollo --callback-host 192.168.1.10 --callback-port 443 \\
    --output-type exe --commands shell,upload,download,mimikatz \\
    --output-file packstation/configs/apollo.json

  # Poseidon Linux agent
  %(prog)s --payload-type poseidon --callback-host 10.0.0.5 --callback-port 80 \\
    --selected-os Linux --output-type exe --commands all
        """
    )

    # Required arguments
    parser.add_argument('--payload-type', required=True,
                        help='Payload type (apollo, poseidon, athena, etc.)')
    parser.add_argument('--callback-host', required=True,
                        help='C2 callback host (URL or IP)')
    parser.add_argument('--callback-port', type=int, required=True,
                        help='C2 callback port')

    # Callback configuration
    parser.add_argument('--callback-interval', type=int, default=3,
                        help='Callback interval in seconds (default: 3)')
    parser.add_argument('--callback-jitter', type=int, default=23,
                        help='Callback jitter percentage (default: 23)')

    # Payload configuration
    parser.add_argument('--selected-os', default='Windows',
                        choices=['Windows', 'Linux', 'macOS'],
                        help='Target operating system (default: Windows)')
    parser.add_argument('--output-type', default='shellcode',
                        choices=['exe', 'dll', 'shellcode'],
                        help='Output type (default: shellcode)')
    parser.add_argument('--shellcode-format', default='Binary',
                        choices=['Binary', 'base64', 'hex'],
                        help='Shellcode format (default: Binary)')

    # Commands
    parser.add_argument('--commands', default='all',
                        help='Commands to include: "all" or comma-separated list (default: all)')

    # Optional parameters
    parser.add_argument('--killdate',
                        help='Payload kill date in YYYY-MM-DD format (default: 1 year from now)')
    parser.add_argument('--user-agent',
                        default='Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
                        help='HTTP User-Agent header')
    parser.add_argument('--encryption-key',
                        help='Custom encryption key (default: aes256_hmac)')
    parser.add_argument('--filename',
                        help='Output filename (default: {payload_type}-payload.bin)')

    # Output options
    parser.add_argument('--output-file',
                        help='Save config to file instead of stdout')
    parser.add_argument('--pretty', action='store_true',
                        help='Pretty-print JSON output')

    args = parser.parse_args()

    # Generate configuration
    config = generate_config(args)

    # Serialize to JSON
    if args.pretty:
        json_output = json.dumps(config, indent=2)
    else:
        json_output = json.dumps(config)

    # Output
    if args.output_file:
        try:
            with open(args.output_file, 'w') as f:
                f.write(json_output)
            print(f"Configuration saved to: {args.output_file}", file=sys.stderr)
        except IOError as e:
            print(f"Error writing to file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Output to stdout for piping
        print(json_output)


if __name__ == "__main__":
    main()
