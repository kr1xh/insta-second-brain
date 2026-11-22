# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "platformdirs>=4",
#   "faster-whisper>=1.1",
#   "pillow>=10.1",
#   "rapidocr>=3.4",
#   "onnxruntime>=1.20",
#   "playwright>=1.48",
#   "filelock>=3.12",
#   "httpx>=0.27",
# ]
# ///
"""Run doughrun's ig.py with a lower OCR rate, without editing doughrun.

Usage: uv run scripts/ig_video.py <path/to/ig.py> <ocr_every> video <file> [ig.py options]

doughrun scans at 10 fps and OCRs every 2nd frame (5 fps). On a slow machine that
dominates analysis time; ocr_every=10 OCRs once a second and still skips near-identical
frames. The dependency list mirrors ig.py's so uv builds the same environment.
"""
import sys
from pathlib import Path


def main() -> int:
    ig_py, ocr_every, *rest = sys.argv[1:]
    scripts = Path(ig_py).resolve().parent
    sys.path.insert(0, str(scripts))
    from iglib import videomap

    videomap.OCR_EVERY = max(1, int(ocr_every))
    import ig

    return ig.main(rest)


if __name__ == "__main__":
    sys.exit(main())
