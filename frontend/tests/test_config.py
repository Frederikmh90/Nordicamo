import os
import unittest


class TestFrontendConfig(unittest.TestCase):
    def test_default_api_base_url(self):
        from config import get_api_base_url

        old = os.environ.pop("NAMO_API_BASE_URL", None)
        try:
            self.assertEqual(get_api_base_url(), "http://localhost:8001")
        finally:
            if old is not None:
                os.environ["NAMO_API_BASE_URL"] = old

    def test_env_api_base_url_strips_trailing_slash(self):
        from config import get_api_base_url

        old = os.environ.get("NAMO_API_BASE_URL")
        os.environ["NAMO_API_BASE_URL"] = "http://example:1234/"
        try:
            self.assertEqual(get_api_base_url(), "http://example:1234")
        finally:
            if old is None:
                os.environ.pop("NAMO_API_BASE_URL", None)
            else:
                os.environ["NAMO_API_BASE_URL"] = old


if __name__ == "__main__":
    unittest.main()
