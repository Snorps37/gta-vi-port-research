"""Check the entry point of a project-authored JSON manifest without running it."""

import argparse
import json
from pathlib import Path, PureWindowsPath
import sys


def check_manifest(manifest: Path) -> str:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    entry = data.get("executable") if isinstance(data, dict) else None
    if not isinstance(entry, str) or not entry.strip():
        raise ValueError("expected an executable path in the manifest")

    # Use Windows path rules on every host so examples behave consistently.
    relative = PureWindowsPath(entry)
    if relative.anchor or ".." in relative.parts:
        raise ValueError("the executable path must stay inside the manifest directory")
    root = manifest.parent.resolve()
    candidate = root.joinpath(*relative.parts).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("the executable resolves outside the manifest directory")
    if not candidate.is_file():
        raise ValueError(f"missing file: {entry}")
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        entry = check_manifest(args.manifest)
    except (ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"file present: {entry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
