import os
import unittest


class TestAnalyticsConfig(unittest.TestCase):
    def test_default_umami_enabled(self):
        from analytics import umami_enabled

        old_url = os.environ.pop("UMAMI_SCRIPT_URL", None)
        old_id = os.environ.pop("UMAMI_WEBSITE_ID", None)
        try:
            self.assertTrue(umami_enabled())
        finally:
            if old_url is not None:
                os.environ["UMAMI_SCRIPT_URL"] = old_url
            if old_id is not None:
                os.environ["UMAMI_WEBSITE_ID"] = old_id

    def test_build_umami_script_tag_contains_required_attrs(self):
        from analytics import build_umami_script_tag

        old_url = os.environ.get("UMAMI_SCRIPT_URL")
        old_id = os.environ.get("UMAMI_WEBSITE_ID")
        old_domains = os.environ.get("UMAMI_DOMAINS")
        os.environ["UMAMI_SCRIPT_URL"] = "https://cloud.umami.is/script.js"
        os.environ["UMAMI_WEBSITE_ID"] = "test-website-id"
        os.environ["UMAMI_DOMAINS"] = "nordicamo.org"
        try:
            tag = build_umami_script_tag()
            self.assertIn('src="https://cloud.umami.is/script.js"', tag)
            self.assertIn('data-website-id="test-website-id"', tag)
            self.assertIn('data-domains="nordicamo.org"', tag)
            self.assertTrue(tag.startswith("<script"))
            self.assertTrue(tag.endswith("</script>"))
        finally:
            if old_url is None:
                os.environ.pop("UMAMI_SCRIPT_URL", None)
            else:
                os.environ["UMAMI_SCRIPT_URL"] = old_url
            if old_id is None:
                os.environ.pop("UMAMI_WEBSITE_ID", None)
            else:
                os.environ["UMAMI_WEBSITE_ID"] = old_id
            if old_domains is None:
                os.environ.pop("UMAMI_DOMAINS", None)
            else:
                os.environ["UMAMI_DOMAINS"] = old_domains

    def test_build_umami_bootstrap_html_contains_runtime_loader(self):
        from analytics import build_umami_bootstrap_html

        old_url = os.environ.get("UMAMI_SCRIPT_URL")
        old_id = os.environ.get("UMAMI_WEBSITE_ID")
        old_domains = os.environ.get("UMAMI_DOMAINS")
        os.environ["UMAMI_SCRIPT_URL"] = "https://cloud.umami.is/script.js"
        os.environ["UMAMI_WEBSITE_ID"] = "test-website-id"
        os.environ["UMAMI_DOMAINS"] = "nordicamo.org,www.nordicamo.org"
        try:
            html = build_umami_bootstrap_html()
            self.assertIn("window.parent", html)
            self.assertIn("targetDoc.createElement('script')", html)
            self.assertIn("data-website-id", html)
            self.assertIn("test-website-id", html)
            self.assertIn("nordicamo.org,www.nordicamo.org", html)
        finally:
            if old_url is None:
                os.environ.pop("UMAMI_SCRIPT_URL", None)
            else:
                os.environ["UMAMI_SCRIPT_URL"] = old_url
            if old_id is None:
                os.environ.pop("UMAMI_WEBSITE_ID", None)
            else:
                os.environ["UMAMI_WEBSITE_ID"] = old_id
            if old_domains is None:
                os.environ.pop("UMAMI_DOMAINS", None)
            else:
                os.environ["UMAMI_DOMAINS"] = old_domains


if __name__ == "__main__":
    unittest.main()
