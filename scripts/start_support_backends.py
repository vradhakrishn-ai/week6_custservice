from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.mock_backends import launch_backends


if __name__ == "__main__":
    processes = launch_backends()
    print("Started support backends. Press Ctrl+C to stop them.")
    try:
        for proc in processes:
            proc.join()
    except KeyboardInterrupt:
        for proc in processes:
            proc.terminate()
        for proc in processes:
            proc.join(timeout=3)
