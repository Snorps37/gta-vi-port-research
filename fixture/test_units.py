import unittest

from fixture.units import frames_to_ms


class FramesToMillisecondsTest(unittest.TestCase):
    def test_whole_seconds(self):
        self.assertEqual(frames_to_ms(120, 60), 2000)

    def test_fractional_millisecond_rounds_down(self):
        self.assertEqual(frames_to_ms(1, 60), 16)

    def test_zero_frames(self):
        self.assertEqual(frames_to_ms(0, 60), 0)

    def test_invalid_inputs(self):
        for frames, fps in [(-1, 60), (1, 0), (1, -1)]:
            with self.subTest(frames=frames, fps=fps):
                with self.assertRaises(ValueError):
                    frames_to_ms(frames, fps)
