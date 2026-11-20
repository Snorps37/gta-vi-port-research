import io
import struct
import unittest
import zlib

from fixture.directory_probe import predicted_pairs


class DirectoryProbeTest(unittest.TestCase):
    def setUp(self):
        self.a = zlib.compress(b"first original record")
        self.b = zlib.compress(b"another original record")
        self.table = bytearray(32)
        struct.pack_into("<II", self.table, 4, 2, len(self.a))
        struct.pack_into("<II", self.table, 20, 5, len(self.b))

    def probe(self, second):
        data = self.table + self.a + bytes(48 - len(self.a)) + second
        return list(predicted_pairs(io.BytesIO(data), 0, 32, unit=16, stride=16))

    def test_both_predictions_match(self):
        self.assertEqual(self.probe(self.b), [((4, 32, len(self.a)), (20, 80, len(self.b)))])

    def test_first_match_cannot_rescue_wrong_second_size(self):
        struct.pack_into("<I", self.table, 24, len(self.b) - 1)
        self.assertEqual(self.probe(self.b), [])

    def test_second_checksum_required(self):
        damaged = self.b[:-1] + bytes([self.b[-1] ^ 1])
        self.assertEqual(self.probe(damaged), [])

    def test_reject_invalid_region(self):
        with self.assertRaises(ValueError):
            list(predicted_pairs(io.BytesIO(b""), 0, 8))
