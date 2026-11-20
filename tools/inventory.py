"""Write a deterministic inventory of regular files as JSON Lines on stdout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile


def fail(error):
    raise error


def linked(info):
    # Windows junctions and other reparse points can lead outside the input.
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def inventory(root, hash_contents):
    if linked(root.lstat()) or not root.is_dir():
        raise ValueError("select a regular directory as the input root")
    for folder, directories, files in os.walk(root, onerror=fail):
        parent = Path(folder)
        directories[:] = sorted(d for d in directories if not linked((parent / d).lstat()))
        for name in sorted(files):
            path = parent / name
            before = path.lstat()
            if linked(before) or not stat.S_ISREG(before.st_mode):
                continue
            row = {"path": path.relative_to(root).as_posix(), "bytes": before.st_size}
            if hash_contents:
                digest = hashlib.sha256()
                with path.open("rb") as source:
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk)
                    after = os.fstat(source.fileno())
                if (not os.path.samestat(before, after) or before.st_size != after.st_size
                        or before.st_mtime_ns != after.st_mtime_ns):
                    raise ValueError(f"file changed while hashing: {path}")
                row["sha256"] = digest.hexdigest()
            yield row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--sha256", action="store_true", help="read and hash file contents")
    args = parser.parse_args()
    try:
        with tempfile.TemporaryFile(mode="w+", encoding="ascii") as pending:
            for row in inventory(args.directory, args.sha256):
                print(json.dumps(row, ensure_ascii=True), file=pending)
            pending.seek(0)
            shutil.copyfileobj(pending, sys.stdout)
    except (OSError, ValueError) as exc:
        print(f"Inventory incomplete: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
