#!/usr/bin/env python3
"""Helper script to encode stdin input using various encoding methods.

Usage:
    echo "data" | encode.py -t base64pwsh
    echo "data" | encode.py -t base64
    echo "data" | encode.py -t urlencoded
    echo "data" | encode.py -t hex

Note: Requires PYTHONPATH to be set to profi's parent directory.
Templates automatically set this using the profi_install_dir variable.
"""

import argparse
import sys

from profi.filters import base64_encode, base64_pwsh, hex_encode, url_encode

# Mapping of encoding types to filter functions
ENCODERS = {
    "base64pwsh": base64_pwsh,
    "base64": base64_encode,
    "urlencoded": url_encode,
    "hex": hex_encode,
}


def main():
    parser = argparse.ArgumentParser(
        description="Encode stdin input using various encoding methods",
        epilog='example: echo "data" | %(prog)s -t TYPE',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-t",
        "--type",
        required=True,
        choices=ENCODERS.keys(),
        help="Encoding type to use",
    )
    args = parser.parse_args()

    # Read from stdin, strip trailing newline
    data = sys.stdin.read().rstrip("\n")

    # Get the appropriate encoder function
    encoder = ENCODERS[args.type]

    # Encode and output
    encoded = encoder(data)
    print(encoded)


if __name__ == "__main__":
    main()
