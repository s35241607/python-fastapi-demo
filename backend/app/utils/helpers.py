def slugify(text: str) -> str:
    """Convert text to a slug-friendly format."""
    return text.lower().replace(" ", "-").replace("/", "-")

def validate_email(email: str) -> bool:
    """Simple email validation."""
    return "@" in email and "." in email.split("@")[-1]