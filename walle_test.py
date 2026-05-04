from __future__ import annotations

import unittest


def main() -> None:
    suite = unittest.defaultTestLoader.discover(
        start_dir="tests",
        pattern="test_*.py",
        top_level_dir=".",
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
