import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient


class TestContactEndpoint(unittest.TestCase):
    def setUp(self):
        from app.main import app

        self.client = TestClient(app)

    def test_contact_sends_email(self):
        with mock.patch("app.services.email_service.smtplib.SMTP") as smtp_mock:
            smtp_instance = smtp_mock.return_value.__enter__.return_value
            os.environ["SMTP_HOST"] = "smtp.example.com"
            os.environ["SMTP_PORT"] = "587"
            os.environ["SMTP_USER"] = "user"
            os.environ["SMTP_PASS"] = "pass"
            os.environ["SMTP_FROM"] = "noreply@example.com"

            response = self.client.post(
                "/api/contact",
                json={
                    "name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "message": "Access request.",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "sent")
            smtp_instance.send_message.assert_called_once()

    def test_contact_missing_smtp_config(self):
        with mock.patch("app.services.email_service.smtplib.SMTP"):
            os.environ.pop("SMTP_HOST", None)
            os.environ.pop("SMTP_FROM", None)
            response = self.client.post(
                "/api/contact",
                json={
                    "name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "message": "Access request.",
                },
            )
            self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
