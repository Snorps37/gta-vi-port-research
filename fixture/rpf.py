"""Verify zlib stream boundaries at a candidate offset in a seekable file."""
import argparse
from pathlib import Path
import zlib

# Keep both the compressed input and the temporary decoded data bounded.
LIMIT = 1024 * 1024
CHUNK = 8192
PAGE = 64 * 1024
MAX_PAGES = 256


def stream_extent(source, start, decoded_limit=LIMIT):
    source.seek(start)
    decoder = zlib.decompressobj()
    consumed = produced = 0
    while consumed < LIMIT:
        block = source.read(min(CHUNK, LIMIT - consumed))
        if not block:
            raise ValueError("incomplete zlib stream")
        try:
            output = decoder.decompress(block, decoded_limit - produced + 1)
        except zlib.error as exc:
            raise ValueError("invalid zlib stream or checksum") from exc
        produced += len(output)
        if produced > decoded_limit:
            raise ValueError("decoded stream exceeds probe limit")
        consumed += len(block)
        if decoder.eof:
            return start + consumed - len(decoder.unused_data), produced
    raise ValueError("compressed stream exceeds probe limit")


def stream_end(source, start):
    return stream_extent(source, start)[0]


def check_start(start):
    if start < 0 or start % 16:
        raise ValueError("candidate offset must be nonnegative and 16-byte aligned")


def next_aligned_stream(source, end):
    following = (end + 15) // 16 * 16
    source.seek(end)
    if source.read(following - end) != bytes(following - end):
        raise ValueError("invalid alignment padding")
    return following


def adjacent_streams(source, start):
    """Return two half-open byte ranges. Only zero alignment padding is accepted."""
    check_start(start)
    end = stream_end(source, start)
    following = next_aligned_stream(source, end)
    return (start, end), (following, stream_end(source, following))


def paged_extent(source, start):
    """Return stored span, decoded size and page count for a run with a short tail."""
    check_start(start)
    at = start
    for count in range(1, MAX_PAGES + 1):
        end, size = stream_extent(source, at, decoded_limit=PAGE)
        if size < PAGE:
            return end - start, (count - 1) * PAGE + size, count
        if count < MAX_PAGES:
            at = next_aligned_stream(source, end)
    raise ValueError("no short terminal page within probe limit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("offset", type=lambda value: int(value, 0))
    parser.add_argument("--paged", action="store_true",
                        help="verify a run of full 64 KiB pages ending in a short page")
    args = parser.parse_args()
    try:
        with args.file.open("rb") as source:
            if args.paged:
                stored, decoded, pages = paged_extent(source, args.offset)
                print(f"stored_span={stored} decoded_size={decoded} pages={pages}")
            else:
                for start, end in adjacent_streams(source, args.offset):
                    print(f"[{start}, {end})")
    except (ValueError, OSError, OverflowError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
