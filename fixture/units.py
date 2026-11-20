"""A self-authored fixture for the Project NATIVE smoke test."""


def frames_to_ms(frames: int, fps: int) -> int:
    """Return floor(milliseconds) for a nonnegative frame count and positive FPS."""
    if frames < 0 or fps <= 0:
        raise ValueError("frames must be nonnegative and fps must be positive")
    return frames * 1000 // fps
