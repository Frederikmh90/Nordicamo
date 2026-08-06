import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestGetAccessPageCopy(unittest.TestCase):
    def test_feedback_copy_invites_features_outlets_and_research_feedback(self):
        from pages.get_access import ACCESS_FEEDBACK_TEXT

        self.assertIn("platform features", ACCESS_FEEDBACK_TEXT)
        self.assertIn("outlet candidates", ACCESS_FEEDBACK_TEXT)
        self.assertIn("observation", ACCESS_FEEDBACK_TEXT)
        self.assertNotIn("monitoring", ACCESS_FEEDBACK_TEXT)
        self.assertIn("research infrastructure", ACCESS_FEEDBACK_TEXT)

    def test_contact_line_names_postdoc_role(self):
        from pathlib import Path

        source = Path(__file__).resolve().parents[1] / "pages" / "get_access.py"
        text = source.read_text(encoding="utf-8")

        self.assertIn("Frederik Henriksen", text)
        self.assertIn("postdoc in the AlterPublics research project", text)

    def test_workshop_request_is_editable_before_email_handoff(self):
        from pathlib import Path

        source = (Path(__file__).resolve().parents[1] / "pages" / "get_access.py").read_text(encoding="utf-8")

        self.assertIn("st.text_area(", source)
        self.assertIn('key="access_request_draft"', source)
        self.assertNotIn("st.code(request_context", source)


if __name__ == "__main__":
    unittest.main()
