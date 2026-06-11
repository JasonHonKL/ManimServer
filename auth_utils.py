import base64
import secrets


def verify_basic(auth_header: str, password: str) -> bool:
    if not auth_header or not password:
        return False
    try:
        scheme, encoded = auth_header.split(" ", 1)
    except ValueError:
        return False
    if scheme.lower() != "basic":
        return False
    expected = base64.b64encode(f"admin:{password}".encode()).decode()
    return secrets.compare_digest(encoded, expected)
