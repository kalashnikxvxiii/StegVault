"""
Secure password generator.
"""

import secrets
import string
from typing import Optional


class PasswordGenerator:
    """
    Cryptographically secure password generator.
    """

    # Character sets
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?"
    AMBIGUOUS = "il1Lo0O"  # Characters that look similar

    def __init__(
        self,
        length: int = 16,
        use_lowercase: bool = True,
        use_uppercase: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True,
        exclude_ambiguous: bool = False,
    ):
        """
        Initialize password generator with options.

        Args:
            length: Password length (default: 16)
            use_lowercase: Include lowercase letters (default: True)
            use_uppercase: Include uppercase letters (default: True)
            use_digits: Include digits (default: True)
            use_symbols: Include symbols (default: True)
            exclude_ambiguous: Exclude ambiguous characters like i, l, 1, L, o, 0, O (default: False)
        """
        self.length = length
        self.use_lowercase = use_lowercase
        self.use_uppercase = use_uppercase
        self.use_digits = use_digits
        self.use_symbols = use_symbols
        self.exclude_ambiguous = exclude_ambiguous

        # Build character set
        self.charset = self._build_charset()

        if not self.charset:
            raise ValueError("At least one character set must be enabled")

    def _build_charset(self) -> str:
        """Build the character set based on options."""
        charset = ""

        if self.use_lowercase:
            charset += self.LOWERCASE
        if self.use_uppercase:
            charset += self.UPPERCASE
        if self.use_digits:
            charset += self.DIGITS
        if self.use_symbols:
            charset += self.SYMBOLS

        # Remove ambiguous characters if requested
        if self.exclude_ambiguous:
            charset = "".join(c for c in charset if c not in self.AMBIGUOUS)

        return charset

    def generate(self) -> str:
        """
        Generate a secure random password.

        Returns:
            Generated password string
        """
        # Use secrets module for cryptographically strong randomness
        password = "".join(secrets.choice(self.charset) for _ in range(self.length))

        # Ensure password meets requirements (has at least one char from each enabled set)
        if not self._meets_requirements(password):
            # Regenerate if requirements not met (rare with good length)
            return self.generate()

        return password

    def _meets_requirements(self, password: str) -> bool:
        """Check if password meets the minimum requirements."""
        if self.use_lowercase and not any(c in self.LOWERCASE for c in password):
            return False
        if self.use_uppercase and not any(c in self.UPPERCASE for c in password):
            return False
        if self.use_digits and not any(c in self.DIGITS for c in password):
            return False
        if self.use_symbols and not any(c in self.SYMBOLS for c in password):
            return False
        return True

    def generate_multiple(self, count: int = 5) -> list[str]:
        """
        Generate multiple passwords.

        Args:
            count: Number of passwords to generate (default: 5)

        Returns:
            List of generated passwords
        """
        return [self.generate() for _ in range(count)]


def generate_password(
    length: int = 16,
    use_lowercase: bool = True,
    use_uppercase: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    """
    Convenience function to generate a single password.

    Args:
        length: Password length (default: 16)
        use_lowercase: Include lowercase letters (default: True)
        use_uppercase: Include uppercase letters (default: True)
        use_digits: Include digits (default: True)
        use_symbols: Include symbols (default: True)
        exclude_ambiguous: Exclude ambiguous characters (default: False)

    Returns:
        Generated password string
    """
    generator = PasswordGenerator(
        length=length,
        use_lowercase=use_lowercase,
        use_uppercase=use_uppercase,
        use_digits=use_digits,
        use_symbols=use_symbols,
        exclude_ambiguous=exclude_ambiguous,
    )
    return generator.generate()


def generate_passphrase(word_count: int = 4, separator: str = "-") -> str:
    """
    Generate a memorable passphrase using random words.

    Note: This is a simple implementation. For production use,
    consider using a proper wordlist (like EFF's diceware list).

    Args:
        word_count: Number of words (default: 4)
        separator: Word separator (default: "-")

    Returns:
        Generated passphrase
    """
    # Simple word list for demonstration
    # In production, use a proper wordlist like EFF's diceware
    word_list = [
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
        "india",
        "juliet",
        "kilo",
        "lima",
        "mike",
        "november",
        "oscar",
        "papa",
        "quebec",
        "romeo",
        "sierra",
        "tango",
        "uniform",
        "victor",
        "whiskey",
        "xray",
        "yankee",
        "zulu",
        "correct",
        "horse",
        "battery",
        "staple",
        "mountain",
        "river",
        "forest",
        "ocean",
        "desert",
        "valley",
        "cloud",
        "thunder",
        "lightning",
        "rainbow",
    ]

    words = [secrets.choice(word_list) for _ in range(word_count)]
    return separator.join(words)


def estimate_entropy(password: str) -> float:
    """
    Estimate password entropy in bits.

    Args:
        password: The password to analyze

    Returns:
        Estimated entropy in bits
    """
    # Count unique character types
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_digit = any(c in string.digits for c in password)
    has_symbol = any(
        c in "!@#$%^&*()-_=+[]{}|;:,.<>?/~`" for c in password
    )

    # Calculate character space size
    charset_size = 0
    if has_lower:
        charset_size += 26
    if has_upper:
        charset_size += 26
    if has_digit:
        charset_size += 10
    if has_symbol:
        charset_size += 32  # Approximate

    # Entropy = log2(charset_size^length)
    import math

    if charset_size == 0:
        return 0.0

    entropy = len(password) * math.log2(charset_size)
    return entropy


def assess_password_strength(password: str) -> tuple[str, float]:
    """
    Assess password strength.

    Args:
        password: The password to assess

    Returns:
        Tuple of (strength_label, entropy_bits)
        strength_label can be: "Weak", "Fair", "Good", "Strong", "Very Strong"
    """
    entropy = estimate_entropy(password)

    if entropy < 28:
        return ("Weak", entropy)
    elif entropy < 36:
        return ("Fair", entropy)
    elif entropy < 60:
        return ("Good", entropy)
    elif entropy < 128:
        return ("Strong", entropy)
    else:
        return ("Very Strong", entropy)
