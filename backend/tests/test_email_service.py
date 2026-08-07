import os
import unittest
from unittest import mock

from app.services import email_service


class TestEmailService(unittest.TestCase):
    def tearDown(self):
        for key in [
            "SENDGRID_API_KEY",
            "SENDGRID_FROM",
            "RESEND_API_KEY",
            "RESEND_FROM",
            "SMTP_FROM",
            "SMTP_HOST",
        ]:
            os.environ.pop(key, None)

    def test_send_contact_email_prefers_sendgrid(self):
        os.environ["SENDGRID_API_KEY"] = "sg-key"
        os.environ["SENDGRID_FROM"] = "noreply@example.com"
        os.environ["RESEND_API_KEY"] = "re-key"
        with mock.patch("app.services.email_service._send_via_sendgrid") as sg_mock:
            with mock.patch("app.services.email_service._send_via_resend") as resend_mock:
                with mock.patch("app.services.email_service._send_via_smtp") as smtp_mock:
                    email_service.send_contact_email("Ada", "ada@example.com", "Hi")
                    sg_mock.assert_called_once()
                    resend_mock.assert_not_called()
                    smtp_mock.assert_not_called()

    def test_send_contact_email_uses_resend_when_api_key_present(self):
        os.environ["RESEND_API_KEY"] = "test-key"
        os.environ["RESEND_FROM"] = "noreply@example.com"
        with mock.patch("app.services.email_service._send_via_sendgrid") as sg_mock:
            with mock.patch("app.services.email_service._send_via_resend") as resend_mock:
                with mock.patch("app.services.email_service._send_via_smtp") as smtp_mock:
                    email_service.send_contact_email("Ada", "ada@example.com", "Hi")
                    sg_mock.assert_not_called()
                    resend_mock.assert_called_once()
                    smtp_mock.assert_not_called()

    def test_send_contact_email_falls_back_to_smtp_without_resend_key(self):
        os.environ["SMTP_HOST"] = "smtp.example.com"
        os.environ["SMTP_FROM"] = "noreply@example.com"
        with mock.patch("app.services.email_service._send_via_smtp") as smtp_mock:
            email_service.send_contact_email("Ada", "ada@example.com", "Hi")
            smtp_mock.assert_called_once()

    def test_resend_request_identifies_nordicamo_client(self):
        os.environ["RESEND_API_KEY"] = "test-key"
        os.environ["RESEND_FROM"] = "requests@nordicamo.org"

        with mock.patch("app.services.email_service.request.urlopen") as urlopen_mock:
            response = urlopen_mock.return_value.__enter__.return_value
            response.status = 200

            email_service._send_via_resend("Ada", "ada@example.com", "Hi", "frmohe@ruc.dk")

            sent_request = urlopen_mock.call_args.args[0]
            self.assertEqual(
                sent_request.get_header("User-agent"),
                "Nordicamo/1.0 (+https://nordicamo.org)",
            )


if __name__ == "__main__":
    unittest.main()
