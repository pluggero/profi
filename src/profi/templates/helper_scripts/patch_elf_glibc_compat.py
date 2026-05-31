#!/usr/bin/env python3
"""
Strip glibc versioned-symbol requirements from a 64-bit LE ELF binary so it
loads on any glibc version that provides the required symbols by name.

What this does:
  1. Zeros the .gnu.version_r section (removes "needs GLIBC_X.Y" records).
  2. Sets every entry in .gnu.version to VER_NDX_GLOBAL (1), telling the
     dynamic linker to resolve each symbol without a version constraint.
  3. Clears DT_VERNEED and DT_VERNEEDNUM tags in the PT_DYNAMIC segment so
     the dynamic linker does not even try to read version requirements.
"""
import struct
import sys


def patch(path: str) -> None:
    with open(path, "rb") as f:
        data = bytearray(f.read())

    if data[:4] != b"\x7fELF":
        sys.exit(f"Not an ELF file: {path}")
    if data[4] != 2 or data[5] != 1:
        sys.exit("Only 64-bit little-endian ELF supported")

    def u16(off: int) -> int: return struct.unpack_from("<H", data, off)[0]
    def u32(off: int) -> int: return struct.unpack_from("<I", data, off)[0]
    def u64(off: int) -> int: return struct.unpack_from("<Q", data, off)[0]
    def s64(off: int) -> int: return struct.unpack_from("<q", data, off)[0]

    e_phoff     = u64(32)
    e_shoff     = u64(40)
    e_phentsize = u16(54)
    e_phnum     = u16(56)
    e_shentsize = u16(58)
    e_shnum     = u16(60)

    SHT_GNU_verneed = 0x6FFFFFFE   # .gnu.version_r
    SHT_GNU_versym  = 0x6FFFFFFF   # .gnu.version
    DT_VERNEED      = 0x6FFFFFFE
    DT_VERNEEDNUM   = 0x6FFFFFFF

    for i in range(e_shnum):
        base      = e_shoff + i * e_shentsize
        sh_type   = u32(base + 4)
        sh_offset = u64(base + 24)
        sh_size   = u64(base + 32)

        if sh_type == SHT_GNU_verneed:
            data[sh_offset: sh_offset + sh_size] = b"\x00" * sh_size

        elif sh_type == SHT_GNU_versym:
            for j in range(sh_size // 2):
                struct.pack_into("<H", data, sh_offset + j * 2, 1)

    for i in range(e_phnum):
        base = e_phoff + i * e_phentsize
        if u32(base) != 2:  # PT_DYNAMIC
            continue
        p_offset = u64(base + 8)
        p_filesz = u64(base + 40)
        off = p_offset
        while off + 16 <= p_offset + p_filesz:
            d_tag = s64(off)
            if d_tag == 0:
                break
            if d_tag in (DT_VERNEED, DT_VERNEEDNUM):
                struct.pack_into("<q", data, off, 0)
                struct.pack_into("<Q", data, off + 8, 0)
            off += 16
        break

    with open(path, "wb") as f:
        f.write(data)

    print(f"Stripped glibc version requirements: {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <elf>")
    patch(sys.argv[1])
