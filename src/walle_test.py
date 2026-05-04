from __future__ import annotations

import unittest
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(project_root / "tests"),
        pattern="test_*.py",
        top_level_dir=str(project_root),
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
