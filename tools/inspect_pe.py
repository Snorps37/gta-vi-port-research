"""Report PE image metadata and ordinary import providers without loading the image."""
import argparse
import json
import mmap
from pathlib import Path
import struct


def inspect(image):
    def read(fmt, offset):
        if offset < 0 or offset + struct.calcsize(fmt) > len(image):
            raise ValueError("truncated PE structure")
        return struct.unpack_from(fmt, image, offset)

    if image[:2] != b"MZ":
        raise ValueError("missing DOS signature")
    pe, = read("<I", 0x3C)
    if image[pe:pe + 4] != b"PE\0\0":
        raise ValueError("missing PE signature")
    machine, count, _, _, _, optional_size, flags = read("<HHIIIHH", pe + 4)
    optional = pe + 24
    end = optional + optional_size
    magic, = read("<H", optional)
    directory_start = {0x10B: 96, 0x20B: 112}.get(magic)
    if directory_start is None or optional_size < directory_start or end > len(image):
        raise ValueError("unsupported or truncated optional header")
    entry, = read("<I", optional + 16)
    headers, = read("<I", optional + 60)
    subsystem, = read("<H", optional + 68)
    directory_count, = read("<I", optional + directory_start - 4)
    if directory_count * 8 > optional_size - directory_start:
        raise ValueError("directory count exceeds optional header")
    if not 1 <= count <= 96 or not end + 40 * count <= headers <= len(image):
        raise ValueError("invalid section table or header extent")
    sections = []
    for i in range(count):
        base = end + 40 * i
        _, rva, size, raw = read("<IIII", base + 8)
        if size and raw + size > len(image):
            raise ValueError("section exceeds file")
        sections.append((rva, size, raw))

    def locate(rva):
        """Return file offset and contiguous file-backed bytes from an RVA."""
        if rva < headers:
            return rva, headers - rva
        for start, size, raw in sections:
            if start <= rva < start + size:
                delta = rva - start
                return raw + delta, size - delta
        raise ValueError("RVA has no file-backed mapping")

    def directory(index):
        if index >= directory_count:
            return 0, 0
        return read("<II", optional + directory_start + index * 8)

    imports, length = directory(1)
    providers = set()
    if bool(imports) != bool(length):
        raise ValueError("incomplete import directory")
    if imports:
        offset, available = locate(imports)
        if length > available:
            raise ValueError("unsupported import directory spanning file mappings")
        for pos in range(offset, offset + length - 19, 20):
            fields = read("<5I", pos)
            if not any(fields):
                break
            if not fields[3]:
                raise ValueError("missing import provider name")
            name, remaining = locate(fields[3])
            stop = image.find(b"\0", name, name + min(remaining, 4096))
            if stop <= name:
                raise ValueError("empty or unterminated import name")
            providers.add(image[name:stop].decode("ascii").lower())
        else:
            raise ValueError("unterminated import descriptor list")
    return {
        "machine": {0x8664: "x64", 0x14C: "x86", 0xAA64: "ARM64"}.get(machine, hex(machine)),
        "pe_format": "PE32+" if magic == 0x20B else "PE32",
        "image_kind": "DLL" if flags & 0x2000 else "non-DLL",
        "subsystem_id": subsystem,
        "entry_point_rva": hex(entry),
        "section_count": count,
        "ordinary_import_providers": sorted(providers),
        "delay_import_directory_declared": all(directory(13)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        with args.file.open("rb") as source:
            with mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ) as image:
                print(json.dumps(inspect(image), indent=2))
    except (ValueError, OSError, OverflowError) as exc:
        parser.exit(1, f"Inspection failed: {exc}\n")


if __name__ == "__main__":
    main()
