"""Minimal public fixture smoke test."""
import unittest


class SmokeTest(unittest.TestCase):
    """Verify the public test environment is operational."""

    def test_fixture(self):
        """Keep a deterministic green baseline."""
        self.assertEqual(2 + 2, 4)


if __name__ == "__main__":
    unittest.main()
