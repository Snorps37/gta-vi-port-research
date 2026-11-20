import io
import random
import unittest
import zlib

from fixture.rpf import LIMIT, adjacent_streams


def pair(first, second):
    a, b = zlib.compress(first), zlib.compress(second)
    start = 32
    end = start + len(a)
    following = end + (-end % 16)
    data = bytes(start) + a + bytes(following - end) + b
    return data, ((start, end), (following, len(data)))


class StreamBoundaryTest(unittest.TestCase):
    def test_ranges_match_writer_with_trailing_data_and_multiple_reads(self):
        data, ranges = pair(random.Random(17).randbytes(25000), b"second")
        self.assertEqual(adjacent_streams(io.BytesIO(data + b"tail"), 32), ranges)

    def test_corruption_in_either_checksum_and_truncation(self):
        data, ranges = pair(b"first", b"second")
        for _, end in ranges:
            damaged = bytearray(data)
            damaged[end - 1] ^= 1
            with self.assertRaises(ValueError):
                adjacent_streams(io.BytesIO(damaged), 32)
        with self.assertRaises(ValueError):
            adjacent_streams(io.BytesIO(data[:-1]), 32)

    def test_nonzero_padding_and_wrong_start(self):
        data, ((_, end), (following, _)) = pair(b"first", b"second")
        self.assertLess(end, following)
        damaged = bytearray(data)
        damaged[end] = 1
        for source, offset in ((damaged, 32), (data, 33), (data, 16)):
            with self.assertRaises(ValueError):
                adjacent_streams(io.BytesIO(source), offset)

    def test_expansion_limit(self):
        data, _ = pair(bytes(LIMIT + 1), b"")
        with self.assertRaisesRegex(ValueError, "decoded"):
            adjacent_streams(io.BytesIO(data), 32)
