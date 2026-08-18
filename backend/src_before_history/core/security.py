import hashlib

def get_password_hash(password: str) -> str:
    """Hash a plaintext password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its SHA-256 hash."""
    return get_password_hash(plain_password) == hashed_password
