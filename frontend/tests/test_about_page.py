import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestAboutPageCopy(unittest.TestCase):
    def test_digital_media_lab_mentions_are_linked(self):
        source = Path(__file__).resolve().parents[1] / "pages" / "about.py"
        text = source.read_text(encoding="utf-8")

        self.assertIn('href="https://digitalmedialab.ruc.dk/"', text)
        self.assertIn("<strong>Digital Media Lab (DML)</strong></a> hosts this platform", text)
        self.assertIn("Department of Communication and Arts - Roskilde University", text)


if __name__ == "__main__":
    unittest.main()
