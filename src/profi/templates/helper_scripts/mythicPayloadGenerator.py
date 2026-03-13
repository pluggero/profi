#!/usr/bin/env python3
"""
Mythic C2 Payload Generator

This script submits payload configurations to the Mythic C2 framework using the
official Mythic Python library, polls for build completion, and downloads the generated payload.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

try:
    from mythic import mythic as mythic_api
except ImportError:
    print("Error: mythic library not found. Install with: pip install mythic", file=sys.stderr)
    sys.exit(1)


class MythicPayloadGenerator:
    def __init__(self, mythic_url, api_token, timeout=300):
        """
        Initialize Mythic API client using official library.

        Args:
            mythic_url: Mythic server URL (e.g., https://mythic.example.com:7443)
            api_token: API authentication token
            timeout: Build timeout in seconds
        """
        from urllib.parse import urlparse

        self.mythic_url = mythic_url.rstrip('/')
        self.api_token = api_token
        self.timeout = timeout

        # Parse the URL to extract components
        parsed = urlparse(mythic_url)
        self.server_ip = parsed.hostname or 'localhost'
        self.server_port = parsed.port
        self.use_ssl = parsed.scheme == 'https'

        self.mythic_instance = None

    async def login(self):
        """Authenticate with Mythic server using API token."""
        try:
            print(f"[*] Authenticating with Mythic server...", file=sys.stderr)

            # Login using API token
            self.mythic_instance = await mythic_api.login(
                apitoken=self.api_token,
                server_ip=self.server_ip,
                server_port=self.server_port,
                ssl=self.use_ssl,
                timeout=self.timeout
            )

            print(f"[+] Successfully authenticated", file=sys.stderr)
            return True

        except Exception as e:
            print(f"[!] Authentication failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return False

    async def create_payload_from_json(self, config):
        """
        Submit payload configuration to Mythic and wait for build completion.

        Args:
            config: Payload configuration dictionary

        Returns:
            Payload UUID if successful, None otherwise
        """
        try:
            print(f"[*] Submitting payload configuration to Mythic...", file=sys.stderr)

            # Extract configuration parameters
            payload_type = config.get('payload_type', 'apollo')
            filename = config.get('filename', 'agent')
            operating_system = config.get('selected_os', 'Windows')

            # Extract commands - handle both list and "all" string
            commands = config.get('commands', [])
            include_all_commands = False
            if commands == "all" or (isinstance(commands, list) and "all" in commands):
                include_all_commands = True
                commands = []

            # Extract C2 profiles
            c2_profiles = config.get('c2_profiles', [])

            # Extract build parameters
            build_parameters = config.get('build_parameters', [])

            # Create payload using the official library with synchronous build
            print(f"[*] Waiting for Mythic to build the payload... (timeout: {self.timeout}s)", file=sys.stderr)
            result = await mythic_api.create_payload(
                mythic=self.mythic_instance,
                payload_type_name=payload_type,
                filename=filename,
                operating_system=operating_system,
                c2_profiles=c2_profiles,
                commands=commands,
                build_parameters=build_parameters,
                include_all_commands=include_all_commands,
                return_on_complete=True,  # Wait for build to complete
                timeout=self.timeout
            )

            # The result should contain the UUID
            if result and 'uuid' in result:
                uuid = result['uuid']
                print(f"[+] Payload built successfully with UUID: {uuid}", file=sys.stderr)
                return uuid
            else:
                print(f"[!] Failed to create payload: {result}", file=sys.stderr)
                return None

        except Exception as e:
            print(f"[!] Payload creation failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None

    async def download_payload_async(self, payload_uuid, output_path):
        """
        Download the generated payload binary.

        Args:
            payload_uuid: Mythic payload UUID
            output_path: Local path to save payload

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"[*] Downloading payload to {output_path}...", file=sys.stderr)

            # Download payload using the official library
            payload_bytes = await mythic_api.download_payload(
                mythic=self.mythic_instance,
                payload_uuid=payload_uuid
            )

            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(output_path, 'wb') as f:
                f.write(payload_bytes)

            file_size = Path(output_path).stat().st_size
            print(f"[+] Payload downloaded successfully! ({file_size} bytes)", file=sys.stderr)
            return True

        except Exception as e:
            print(f"[!] Download failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return False

    async def generate_from_config_async(self, config, output_path):
        """
        Complete workflow: login, create payload (with build wait), and download.

        Args:
            config: Payload configuration dictionary
            output_path: Local path to save payload

        Returns:
            True if successful, False otherwise
        """
        # Step 1: Login
        if not await self.login():
            return False

        # Step 2: Create payload (waits for build automatically)
        payload_uuid = await self.create_payload_from_json(config)
        if not payload_uuid:
            return False

        # Step 3: Download payload
        return await self.download_payload_async(payload_uuid, output_path)

    def generate_from_config(self, config, output_path):
        """
        Synchronous wrapper for the async generate workflow.

        Args:
            config: Payload configuration dictionary
            output_path: Local path to save payload

        Returns:
            True if successful, False otherwise
        """
        return asyncio.run(self.generate_from_config_async(config, output_path))


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mythic C2 payload from configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from piped config
  mythicConfigGenerator.py --payload-type apollo ... | \\
    %(prog)s --mythic-url https://mythic.local --api-token TOKEN \\
      --stdin --output packstation/outbound/agent.bin

  # Generate from saved config file
  %(prog)s --mythic-url https://mythic.local --api-token TOKEN \\
    --config-file packstation/configs/apollo.json \\
    --output packstation/outbound/agent.bin
        """
    )

    # Mythic API configuration
    parser.add_argument('--mythic-url', required=True,
                        help='Mythic server URL (e.g., https://mythic.example.com)')

    # API token (mutually exclusive)
    token_group = parser.add_mutually_exclusive_group(required=True)
    token_group.add_argument('--api-token',
                             help='Mythic API authentication token')
    token_group.add_argument('--api-token-file',
                             help='Path to file containing API token')

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--config-file',
                             help='Path to payload configuration JSON file')
    input_group.add_argument('--stdin', action='store_true',
                             help='Read configuration from stdin')

    # Output configuration
    parser.add_argument('--output', required=True,
                        help='Output path for generated payload')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Build timeout in seconds (default: 300)')
    parser.add_argument('--ssl-verify', action='store_true',
                        help='Verify SSL certificates (default: disabled for self-signed certs)')

    args = parser.parse_args()

    # Read API token
    try:
        if args.api_token_file:
            print(f"[*] Reading API token from {args.api_token_file}...", file=sys.stderr)
            with open(args.api_token_file, 'r') as f:
                api_token = f.read().strip()
        else:
            api_token = args.api_token
    except FileNotFoundError:
        print(f"[!] Token file not found: {args.api_token_file}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"[!] Error reading token file: {e}", file=sys.stderr)
        sys.exit(1)

    # Read configuration
    try:
        if args.stdin:
            print("[*] Reading configuration from stdin...", file=sys.stderr)
            config_json = sys.stdin.read()
        else:
            print(f"[*] Reading configuration from {args.config_file}...", file=sys.stderr)
            with open(args.config_file, 'r') as f:
                config_json = f.read()

        config = json.loads(config_json)

    except FileNotFoundError:
        print(f"[!] Config file not found: {args.config_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[!] Invalid JSON configuration: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"[!] Error reading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize generator with official Mythic library
    generator = MythicPayloadGenerator(
        mythic_url=args.mythic_url,
        api_token=api_token,
        timeout=args.timeout
    )

    # Generate payload
    success = generator.generate_from_config(config, args.output)

    if success:
        print(f"[+] Payload generation complete: {args.output}", file=sys.stderr)
        sys.exit(0)
    else:
        print(f"[!] Payload generation failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
