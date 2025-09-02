"""Password hashing utilities using passlib and bcrypt."""

from passlib.context import CryptContext

# Create password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: Plain text password to verify
        hashed: Hashed password to check against

    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(password, hashed)
