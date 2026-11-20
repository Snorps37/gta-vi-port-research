"""Test a narrow directory layout against two independently framed zlib streams."""
import argparse
from pathlib import Path
from struct import Struct

from fixture.rpf import LIMIT, stream_end

PAIR = Struct("<II")


def predicted_pairs(source, table_start, table_end, *, base=0, unit=1, stride=8):
    """Yield matching rows as (row offset, predicted start, predicted size) pairs."""
    source.seek(0, 2)
    file_size = source.tell()
    if not (0 <= table_start <= table_end <= file_size and table_end - table_start <= LIMIT):
        raise ValueError("invalid or oversized table region")
    if base < 0 or unit < 1 or stride < PAIR.size or stride % 4:
        raise ValueError("invalid address base, unit, or row stride")
    source.seek(table_start)
    table = source.read(table_end - table_start)
    for row in range(0, len(table) - stride - PAIR.size + 1, 4):
        # Read both predictions before consulting any payload bytes.
        predictions = []
        for index in (row, row + stride):
            offset, size = PAIR.unpack_from(table, index)
            predictions.append((table_start + index, base + offset * unit, size))
        (_, a, n), (_, b, m) = predictions
        if not (0 < n <= LIMIT and 0 < m <= LIMIT and table_end <= a and
                a + n <= b and b + m <= file_size):
            continue
        try:
            if stream_end(source, a) == a + n and stream_end(source, b) == b + m:
                yield tuple(predictions)
        except ValueError:
            continue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    for name in ("table_start", "table_end"):
        parser.add_argument(name, type=lambda s: int(s, 0))
    for name, default in (("base", 0), ("unit", 1), ("stride", 8)):
        parser.add_argument("--" + name, type=lambda s: int(s, 0), default=default)
    args = vars(parser.parse_args())
    path = args.pop("file")
    found = False
    try:
        with path.open("rb") as source:
            for pair in predicted_pairs(source, **args):
                print(pair)
                found = True
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")
    if not found:
        parser.exit(1, "No matching consecutive rows for this layout.\n")


if __name__ == "__main__":
    main()
