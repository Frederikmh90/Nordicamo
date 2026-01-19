import os
import smtplib
from email.message import EmailMessage


def send_contact_email(name: str, email: str, message: str, to_address: str = "frmohe@ruc.dk") -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_address = os.getenv("SMTP_FROM")

    if password:
        password = password.replace("\xa0", " ").strip()
    if not host or not from_address:
        raise RuntimeError("SMTP_HOST and SMTP_FROM must be set")

    msg = EmailMessage()
    msg["Subject"] = "NAMO data access request"
    msg["From"] = from_address
    msg["To"] = to_address
    msg.set_content(
        "\n".join(
            [
                "New data access request:",
                "",
                f"Name: {name}",
                f"Email: {email}",
                "",
                "Message:",
                message,
            ]
        )
    )

    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)
