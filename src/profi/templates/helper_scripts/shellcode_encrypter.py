import argparse


def caesar_transform(data: bytes, key: int = 2) -> bytes:
    return bytes(((b + key) & 0xFF) for b in data)


def xor_transform(data: bytes, key: int = 0xCA) -> bytes:
    return bytes(b ^ key for b in data)


def _encrypt_file(
    input_path: str,
    output_path: str,
    transform,
    key: int,
    chunk_size: int = 64 * 1024,
):
    with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
        while True:
            chunk = fin.read(chunk_size)
            if not chunk:
                break
            fout.write(transform(chunk, key))


def to_c_buffer(data: bytes, var_name: str = "buf", width: int = 12) -> str:
    lines = [f"unsigned char {var_name}[] = {{"]
    for i in range(0, len(data), width):
        row = ", ".join(f"0x{b:02x}" for b in data[i : i + width])
        terminator = "," if i + width < len(data) else ""
        lines.append(f"    {row}{terminator}")
    lines.append("};")
    lines.append(f"unsigned int {var_name}_len = {len(data)};")
    return "\n".join(lines)


def parse_key(value: str) -> int:
    return int(value, 0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shellcode_encrypter.py",
        description="Encrypt a file using XOR or Caesar, optionally emitting a C-style unsigned char[] buffer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  shellcode_encrypter.py -m xor    -i shell.bin -o shell.enc -k 0xCA\n"
            "  shellcode_encrypter.py -m caesar -i shell.bin -o shell.enc -k 2\n"
            "  shellcode_encrypter.py -m xor    -i shell.bin --c-style --var-name payload\n"
            "  shellcode_encrypter.py -m xor    -i shell.bin --c-style -o shell.h --width 16\n"
        ),
    )
    parser.add_argument(
        "-m", "--mode", choices=["xor", "caesar"], required=True, help="Encryption mode."
    )
    parser.add_argument("-i", "--input", required=True, help="Input file path.")
    parser.add_argument(
        "-o",
        "--output",
        help="Output path. Required for binary output. Optional with --c-style "
        "(defaults to stdout).",
    )
    parser.add_argument(
        "-k",
        "--key",
        type=parse_key,
        default=None,
        help="Integer key (accepts 0x hex, 0o octal, 0b binary). "
        "Defaults: 0xCA for xor, 2 for caesar.",
    )
    parser.add_argument(
        "-c",
        "--c-style",
        action="store_true",
        help="Emit encrypted bytes as a C-style unsigned char[] buffer "
        "instead of raw binary.",
    )
    parser.add_argument(
        "--var-name",
        default="buf",
        help="Variable name for --c-style output (default: buf).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=12,
        help="Bytes per line in --c-style output (default: 12).",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    key = args.key if args.key is not None else (0xCA if args.mode == "xor" else 2)
    transform = xor_transform if args.mode == "xor" else caesar_transform

    if args.c_style:
        with open(args.input, "rb") as fin:
            encoded = transform(fin.read(), key)
        text = to_c_buffer(encoded, args.var_name, args.width)
        if args.output:
            with open(args.output, "w") as fout:
                fout.write(text + "\n")
        else:
            print(text)
        return

    if not args.output:
        parser.error("-o/--output is required unless --c-style is used")

    _encrypt_file(args.input, args.output, transform, key)


if __name__ == "__main__":
    main()
