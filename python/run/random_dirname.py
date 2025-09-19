import random
import string

def random_dirname(length: int = 12) -> str:
    """
    Generate a random string safe for use as a directory name.
    Default length = 12 characters.
    Allowed chars: lowercase, uppercase, digits, underscore, hyphen.
    """
    safe_chars = string.ascii_letters
    return ''.join(random.choice(safe_chars) for _ in range(length))