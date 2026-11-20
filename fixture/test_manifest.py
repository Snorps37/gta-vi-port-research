"""Verify both public sample manifests and the package-directory boundary."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fixture.manifest import check_manifest


EXAMPLES = Path(__file__).parent / "examples"


class ManifestTest(unittest.TestCase):
    def test_present_example(self):
        self.assertEqual(check_manifest(EXAMPLES / "present.json"), "demo.py")

    def test_missing_example_names_the_file(self):
        with self.assertRaisesRegex(ValueError, r"missing file: absent\.py"):
            check_manifest(EXAMPLES / "missing.json")

    def test_parent_path_rejected(self):
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps({"executable": "../outside.py"}))
            with self.assertRaisesRegex(ValueError, "inside the manifest directory"):
                check_manifest(manifest)
