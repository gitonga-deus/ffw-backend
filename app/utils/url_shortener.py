"""
URL shortener utility for creating short verification links.
"""
import secrets
import string


def generate_short_code(length: int = 6) -> str:
    """
    Generate a random short code for URL shortening.
    
    Args:
        length: Length of the short code (default: 6)
        
    Returns:
        Random alphanumeric short code
    """
    # Use alphanumeric characters (excluding similar-looking ones)
    alphabet = string.ascii_letters + string.digits
    # Remove confusing characters: 0, O, I, l, 1
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('l', '').replace('1', '')
    
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_short_url(base_url: str, cert_id: str) -> str:
    """
    Create a shortened URL for certificate verification.
    
    Args:
        base_url: Base URL of the frontend (e.g., "https://example.com")
        cert_id: Certification ID
        
    Returns:
        Shortened URL
    """
    # Generate a short code based on cert_id
    # Extract the hex part from cert_id (e.g., "CERT-1763384481-398156B9" -> "398156B9")
    parts = cert_id.split('-')
    if len(parts) >= 3:
        hex_part = parts[2]
        # Use first 6 characters of the hex part
        short_code = hex_part[:6].upper()
    else:
        # Fallback: generate random short code
        short_code = generate_short_code(6).upper()
    
    # Create short URL
    short_url = f"{base_url}/v/{short_code}"
    
    return short_url
