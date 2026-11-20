"""Verify two adjacent zlib streams at a candidate offset in a seekable file."""
import argparse
from pathlib import Path
import zlib

# Keep both the compressed input and the temporary decoded data bounded.
LIMIT = 1024 * 1024
CHUNK = 8192


def stream_end(source, start):
    source.seek(start)
    decoder = zlib.decompressobj()
    consumed = produced = 0
    while consumed < LIMIT:
        block = source.read(min(CHUNK, LIMIT - consumed))
        if not block:
            raise ValueError("incomplete zlib stream")
        try:
            output = decoder.decompress(block, LIMIT - produced + 1)
        except zlib.error as exc:
            raise ValueError("invalid zlib stream or checksum") from exc
        produced += len(output)
        if produced > LIMIT:
            raise ValueError("decoded stream exceeds probe limit")
        consumed += len(block)
        if decoder.eof:
            return start + consumed - len(decoder.unused_data)
    raise ValueError("compressed stream exceeds probe limit")


def adjacent_streams(source, start):
    """Return two half-open byte ranges. Only zero alignment padding is accepted."""
    if start < 0 or start % 16:
        raise ValueError("candidate offset must be nonnegative and 16-byte aligned")
    end = stream_end(source, start)
    following = (end + 15) // 16 * 16
    source.seek(end)
    if source.read(following - end) != bytes(following - end):
        raise ValueError("invalid alignment padding")
    return (start, end), (following, stream_end(source, following))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("offset", type=lambda value: int(value, 0))
    args = parser.parse_args()
    try:
        with args.file.open("rb") as source:
            for start, end in adjacent_streams(source, args.offset):
                print(f"[{start}, {end})")
    except (ValueError, OSError, OverflowError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
