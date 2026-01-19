from urllib.parse import quote


def build_access_mailto(name: str, email: str, request: str, to_address: str = "frmohe@ruc.dk") -> str:
    subject = "NAMO data access request"
    body = "\n".join(
        [
            "Hello,",
            "",
            "I would like to request access to NAMO data.",
            "",
            f"Name: {name}",
            f"Email: {email}",
            "",
            "Request details:",
            request,
            "",
            "Thank you.",
        ]
    )
    subject_encoded = quote(subject)
    body_encoded = quote(body)
    return f"mailto:{to_address}?subject={subject_encoded}&body={body_encoded}"
