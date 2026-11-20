import io
import random
import unittest
import zlib

from fixture.rpf import LIMIT, PAGE, adjacent_streams, paged_extent


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

    def test_page_run_covers_padding_and_short_tail(self):
        data, _ = pair(bytes(PAGE), b"tail")
        self.assertEqual(paged_extent(io.BytesIO(data + b"unrelated"), 32),
                         (len(data) - 32, PAGE + 4, 2))

    def test_page_run_requires_a_valid_short_tail(self):
        full, ranges = pair(bytes(PAGE), bytes(PAGE))
        short, _ = pair(bytes(PAGE), b"tail")
        for data in (full, short[:-1], short[:ranges[0][1]]):
            with self.subTest(length=len(data)), self.assertRaises(ValueError):
                paged_extent(io.BytesIO(data), 32)

    def test_page_run_rejects_excess_compressed_input(self):
        short = zlib.compress(b"tail")
        # Insert non-final empty stored blocks before the original deflate data.
        stream = short[:2] + bytes.fromhex("000000ffff") * PAGE + short[2:]
        self.assertEqual(zlib.decompress(stream), b"tail")
        with self.assertRaisesRegex(ValueError, "compressed"):
            paged_extent(io.BytesIO(stream), 0)
