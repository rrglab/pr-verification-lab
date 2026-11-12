"""Synthetic PR fixture for verifying review and CI automation."""
import unittest


class PublicPRTest(unittest.TestCase):
    """A deterministic, self-contained public test."""

    def test_safe_fixture(self):
        """Confirm that the isolated test runner executes PR tests."""
        self.assertTrue("quality-factory".startswith("quality"))


if __name__ == "__main__":
    unittest.main()
