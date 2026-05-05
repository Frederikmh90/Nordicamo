import os
import smtplib
import json
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from urllib import error, request


def send_contact_email(name: str, email: str, message: str, to_address: str = "frmohe@ruc.dk") -> None:
    errors = []

    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    if sendgrid_api_key:
        try:
            _send_via_sendgrid(name=name, email=email, message=message, to_address=to_address)
            return
        except RuntimeError as exc:
            errors.append(str(exc))

    resend_api_key = os.getenv("RESEND_API_KEY")
    if resend_api_key:
        try:
            _send_via_resend(name=name, email=email, message=message, to_address=to_address)
            return
        except RuntimeError as exc:
            errors.append(str(exc))

    try:
        _send_via_smtp(name=name, email=email, message=message, to_address=to_address)
        return
    except RuntimeError as exc:
        errors.append(str(exc))

    raise RuntimeError(" | ".join(errors) if errors else "Email delivery failed")


def _build_contact_body(name: str, email: str, message: str) -> str:
    return "\n".join(
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


def _send_via_resend(name: str, email: str, message: str, to_address: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    from_address = os.getenv("RESEND_FROM") or os.getenv("SMTP_FROM")
    target_address = os.getenv("RESEND_TO") or to_address
    timeout_s = float(os.getenv("RESEND_TIMEOUT_SECONDS", "8"))

    if not api_key or not from_address:
        raise RuntimeError("RESEND_API_KEY and RESEND_FROM (or SMTP_FROM) must be set")

    payload = {
        "from": from_address,
        "to": [target_address],
        "subject": "Nordicamo data access request",
        "text": _build_contact_body(name=name, email=email, message=message),
        "reply_to": email,
    }
    req = request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_s) as resp:
            status = getattr(resp, "status", 200)
            if status >= 400:
                raise RuntimeError(f"Resend API failed with status {status}")
    except error.HTTPError as exc:
        raise RuntimeError(f"Resend API failed with status {exc.code}") from exc
    except Exception as exc:
        raise RuntimeError(f"Resend delivery failed: {exc.__class__.__name__}") from exc


def _send_via_sendgrid(name: str, email: str, message: str, to_address: str) -> None:
    api_key = os.getenv("SENDGRID_API_KEY")
    from_address = os.getenv("SENDGRID_FROM") or os.getenv("RESEND_FROM") or os.getenv("SMTP_FROM")
    target_address = os.getenv("SENDGRID_TO") or to_address
    timeout_s = float(os.getenv("SENDGRID_TIMEOUT_SECONDS", "8"))

    if not api_key or not from_address:
        raise RuntimeError("SENDGRID_API_KEY and SENDGRID_FROM (or RESEND_FROM/SMTP_FROM) must be set")

    payload = {
        "personalizations": [{"to": [{"email": target_address}], "subject": "Nordicamo data access request"}],
        "from": {"email": from_address},
        "reply_to": {"email": email},
        "content": [{"type": "text/plain", "value": _build_contact_body(name=name, email=email, message=message)}],
    }
    req = request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_s) as resp:
            status = getattr(resp, "status", 202)
            if status >= 400:
                raise RuntimeError(f"SendGrid API failed with status {status}")
    except error.HTTPError as exc:
        raise RuntimeError(f"SendGrid API failed with status {exc.code}") from exc
    except Exception as exc:
        raise RuntimeError(f"SendGrid delivery failed: {exc.__class__.__name__}") from exc


def _send_via_smtp(name: str, email: str, message: str, to_address: str) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_address = os.getenv("SMTP_FROM")
    timeout_s = float(os.getenv("SMTP_TIMEOUT_SECONDS", "5"))

    if password:
        password = password.replace("\xa0", " ").strip()
    if not host or not from_address:
        raise RuntimeError("SMTP_HOST and SMTP_FROM must be set")

    msg = EmailMessage()
    msg["Subject"] = "Nordicamo data access request"
    msg["From"] = from_address
    msg["To"] = to_address
    msg.set_content(_build_contact_body(name=name, email=email, message=message))

    try:
        # Always set a timeout: the server may not have outbound internet access,
        # and we must not hang the API worker on a blocked SMTP connect.
        with smtplib.SMTP(host, port, timeout=timeout_s) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
    except Exception as exc:
        raise RuntimeError(f"Email delivery failed: {exc.__class__.__name__}") from exc


def queue_contact_request(name: str, email: str, message: str) -> Path:
    """Persist contact request locally when SMTP delivery is unavailable."""
    fallback_path = os.getenv(
        "CONTACT_REQUESTS_FALLBACK_PATH",
        "/home/frede/NAMO_nov25/backend/logs/contact_requests.jsonl",
    )
    out_path = Path(fallback_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "email": email,
        "message": message,
    }
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return out_path
