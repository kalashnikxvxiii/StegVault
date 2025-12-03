# API Reference

Complete API documentation for StegVault v0.7.1.

## Table of Contents

- [Application Layer](#application-layer) - **NEW in v0.6.1**
  - [CryptoController](#cryptocontroller)
  - [VaultController](#vaultcontroller)
- [Core Modules](#core-modules)
  - [stegvault.crypto](#stegvaultcrypto)
  - [stegvault.vault](#stegvaultvault)
  - [stegvault.stego](#stegvaultstego)
  - [stegvault.gallery](#stegvaultgallery)
  - [stegvault.utils](#stegvaultutils)

---

## Application Layer

### CryptoController

**NEW in v0.6.1**: High-level encryption controller with structured results.

```python
from stegvault.app.controllers import CryptoController
```

#### Constructor

```python
def __init__(self, config: Optional[Config] = None):
    """Initialize CryptoController.

    Args:
        config: Optional configuration object. If None, uses default config.
    """
```

#### encrypt()

```python
def encrypt(
    self,
    data: bytes,
    passphrase: str
) -> EncryptionResult:
    """Encrypt data with passphrase.

    Args:
        data: Binary data to encrypt
        passphrase: Encryption passphrase

    Returns:
        EncryptionResult with:
        - ciphertext (bytes): Encrypted data
        - salt (bytes): 16-byte Argon2id salt
        - nonce (bytes): 24-byte XChaCha20 nonce
        - success (bool): True if encryption succeeded
        - error (Optional[str]): Error message if failed

    Example:
        >>> controller = CryptoController()
        >>> result = controller.encrypt(b"secret data", "passphrase")
        >>> if result.success:
        ...     print(f"Encrypted: {result.ciphertext.hex()[:20]}...")
    """
```

#### decrypt()

```python
def decrypt(
    self,
    ciphertext: bytes,
    salt: bytes,
    nonce: bytes,
    passphrase: str
) -> DecryptionResult:
    """Decrypt data with passphrase.

    Args:
        ciphertext: Encrypted data
        salt: 16-byte Argon2id salt
        nonce: 24-byte XChaCha20 nonce
        passphrase: Decryption passphrase

    Returns:
        DecryptionResult with:
        - plaintext (bytes): Decrypted data
        - success (bool): True if decryption succeeded
        - error (Optional[str]): Error message if failed

    Example:
        >>> result = controller.decrypt(ciphertext, salt, nonce, "passphrase")
        >>> if result.success:
        ...     print(f"Decrypted: {result.plaintext}")
    """
```

#### encrypt_with_payload()

```python
def encrypt_with_payload(
    self,
    data: bytes,
    passphrase: str
) -> Tuple[bytes, bool, Optional[str]]:
    """Encrypt data and serialize to payload format.

    Args:
        data: Binary data to encrypt
        passphrase: Encryption passphrase

    Returns:
        Tuple of (payload, success, error) where:
        - payload (bytes): Serialized payload (Magic|Salt|Nonce|Length|Ciphertext|Tag)
        - success (bool): True if succeeded
        - error (Optional[str]): Error message if failed

    Example:
        >>> payload, success, error = controller.encrypt_with_payload(
        ...     b"data", "pass"
        ... )
        >>> if success:
        ...     print(f"Payload size: {len(payload)} bytes")
    """
```

#### decrypt_from_payload()

```python
def decrypt_from_payload(
    self,
    payload: bytes,
    passphrase: str
) -> Tuple[bytes, bool, Optional[str]]:
    """Parse payload and decrypt data.

    Args:
        payload: Serialized payload from encrypt_with_payload()
        passphrase: Decryption passphrase

    Returns:
        Tuple of (plaintext, success, error) where:
        - plaintext (bytes): Decrypted data
        - success (bool): True if succeeded
        - error (Optional[str]): Error message if failed

    Example:
        >>> data, success, error = controller.decrypt_from_payload(
        ...     payload, "pass"
        ... )
        >>> if success:
        ...     print(f"Decrypted: {data}")
    """
```

---

### VaultController

**NEW in v0.6.1**: High-level vault management controller.

```python
from stegvault.app.controllers import VaultController
```

#### Constructor

```python
def __init__(self, config: Optional[Config] = None):
    """Initialize VaultController.

    Args:
        config: Optional configuration object. If None, uses default config.
    """
```

#### load_vault()

```python
def load_vault(
    self,
    image_path: str,
    passphrase: str
) -> VaultLoadResult:
    """Load vault from image file.

    Args:
        image_path: Path to stego image containing vault
        passphrase: Vault encryption passphrase

    Returns:
        VaultLoadResult with:
        - vault (Optional[Vault]): Loaded vault object
        - success (bool): True if load succeeded
        - error (Optional[str]): Error message if failed

    Example:
        >>> controller = VaultController()
        >>> result = controller.load_vault("vault.png", "passphrase")
        >>> if result.success:
        ...     vault = result.vault
        ...     print(f"Loaded {len(vault.entries)} entries")
    """
```

#### save_vault()

```python
def save_vault(
    self,
    vault: Vault,
    output_path: str,
    passphrase: str,
    cover_image: Optional[str] = None
) -> VaultSaveResult:
    """Save vault to image file.

    Args:
        vault: Vault object to save
        output_path: Path for output stego image
        passphrase: Encryption passphrase
        cover_image: Optional cover image path (generates default if None)

    Returns:
        VaultSaveResult with:
        - output_path (str): Path to saved stego image
        - success (bool): True if save succeeded
        - error (Optional[str]): Error message if failed

    Example:
        >>> result = controller.save_vault(
        ...     vault, "vault.png", "passphrase", cover_image="cover.png"
        ... )
        >>> if result.success:
        ...     print(f"Saved to: {result.output_path}")
    """
```

#### create_new_vault()

```python
def create_new_vault(
    self,
    key: str,
    password: str,
    username: Optional[str] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[List[str]] = None,
    totp_secret: Optional[str] = None
) -> Tuple[Vault, bool, Optional[str]]:
    """Create new vault with first entry.

    Args:
        key: Entry key (e.g., "gmail")
        password: Entry password
        username: Optional username
        url: Optional URL
        notes: Optional notes
        tags: Optional tags list
        totp_secret: Optional TOTP secret

    Returns:
        Tuple of (vault, success, error) where:
        - vault (Vault): New vault with first entry
        - success (bool): True if creation succeeded
        - error (Optional[str]): Error message if failed

    Example:
        >>> vault, success, error = controller.create_new_vault(
        ...     key="gmail",
        ...     password="secret123",
        ...     username="user@gmail.com",
        ...     tags=["email", "personal"]
        ... )
        >>> if success:
        ...     print(f"Created vault with {len(vault.entries)} entry")
    """
```

#### add_vault_entry()

```python
def add_vault_entry(
    self,
    vault: Vault,
    key: str,
    password: str,
    username: Optional[str] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[List[str]] = None,
    totp_secret: Optional[str] = None
) -> Tuple[Vault, bool, Optional[str]]:
    """Add entry to existing vault.

    Args:
        vault: Existing vault
        key: Entry key
        password: Entry password
        username: Optional username
        url: Optional URL
        notes: Optional notes
        tags: Optional tags list
        totp_secret: Optional TOTP secret

    Returns:
        Tuple of (updated_vault, success, error)

    Example:
        >>> vault, success, error = controller.add_vault_entry(
        ...     vault, key="github", password="pwd", username="user"
        ... )
    """
```

#### get_vault_entry()

```python
def get_vault_entry(
    self,
    vault: Vault,
    key: str
) -> EntryResult:
    """Get entry from vault by key.

    Args:
        vault: Vault to search
        key: Entry key to find

    Returns:
        EntryResult with:
        - entry (Optional[VaultEntry]): Found entry
        - success (bool): True if found
        - error (Optional[str]): Error if not found

    Example:
        >>> result = controller.get_vault_entry(vault, "gmail")
        >>> if result.success:
        ...     print(f"Password: {result.entry.password}")
    """
```

#### update_vault_entry()

```python
def update_vault_entry(
    self,
    vault: Vault,
    key: str,
    password: Optional[str] = None,
    username: Optional[str] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[List[str]] = None,
    totp_secret: Optional[str] = None
) -> Tuple[Vault, bool, Optional[str]]:
    """Update existing vault entry.

    Args:
        vault: Vault containing entry
        key: Entry key to update
        password: New password (optional)
        username: New username (optional)
        url: New URL (optional)
        notes: New notes (optional)
        tags: New tags (optional)
        totp_secret: New TOTP secret (optional)

    Returns:
        Tuple of (updated_vault, success, error)

    Example:
        >>> vault, success, error = controller.update_vault_entry(
        ...     vault, key="gmail", password="new_password"
        ... )
    """
```

#### delete_vault_entry()

```python
def delete_vault_entry(
    self,
    vault: Vault,
    key: str
) -> Tuple[Vault, bool, Optional[str]]:
    """Delete entry from vault.

    Args:
        vault: Vault containing entry
        key: Entry key to delete

    Returns:
        Tuple of (updated_vault, success, error)

    Example:
        >>> vault, success, error = controller.delete_vault_entry(
        ...     vault, "old_entry"
        ... )
    """
```

#### list_vault_entries()

```python
def list_vault_entries(
    self,
    vault: Vault
) -> List[str]:
    """List all entry keys in vault.

    Args:
        vault: Vault to list

    Returns:
        List of entry keys

    Example:
        >>> keys = controller.list_vault_entries(vault)
        >>> print(f"Entries: {', '.join(keys)}")
    """
```

#### check_image_capacity()

```python
def check_image_capacity(
    self,
    image_path: str
) -> Tuple[int, bool, Optional[str]]:
    """Check image capacity for vault storage.

    Args:
        image_path: Path to image file

    Returns:
        Tuple of (capacity, success, error) where:
        - capacity (int): Max payload size in bytes
        - success (bool): True if check succeeded
        - error (Optional[str]): Error message if failed

    Example:
        >>> capacity, success, error = controller.check_image_capacity(
        ...     "image.png"
        ... )
        >>> if success:
        ...     print(f"Capacity: {capacity} bytes")
    """
```

---

## Core Modules

### stegvault.crypto

Cryptographic operations module.

#### encrypt_data()

```python
def encrypt_data(
    plaintext: bytes,
    passphrase: str,
    time_cost: int = 3,
    memory_cost: int = 65536,
    parallelism: int = 4
) -> Tuple[bytes, bytes, bytes]:
    """Encrypt data using XChaCha20-Poly1305 AEAD.

    Args:
        plaintext: Data to encrypt
        passphrase: Encryption passphrase for key derivation
        time_cost: Argon2id time cost (iterations)
        memory_cost: Argon2id memory cost (KB)
        parallelism: Argon2id parallelism (threads)

    Returns:
        Tuple of (ciphertext, salt, nonce) where:
        - ciphertext (bytes): Encrypted data including AEAD tag
        - salt (bytes): 16-byte Argon2id salt
        - nonce (bytes): 24-byte XChaCha20 nonce

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> from stegvault.crypto import encrypt_data
        >>> plaintext = b"my secret password"
        >>> passphrase = "strongpassphrase123"
        >>> ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)
    """
```

#### decrypt_data()

```python
def decrypt_data(
    ciphertext: bytes,
    passphrase: str,
    salt: bytes,
    nonce: bytes,
    time_cost: int = 3,
    memory_cost: int = 65536,
    parallelism: int = 4
) -> bytes:
    """Decrypt data encrypted with encrypt_data().

    Args:
        ciphertext: Encrypted data (including AEAD tag)
        passphrase: Encryption passphrase
        salt: 16-byte Argon2id salt from encryption
        nonce: 24-byte nonce from encryption
        time_cost: Argon2id time cost (must match encryption)
        memory_cost: Argon2id memory cost (must match encryption)
        parallelism: Argon2id parallelism (must match encryption)

    Returns:
        Decrypted plaintext as bytes

    Raises:
        ValueError: If decryption/authentication fails

    Example:
        >>> from stegvault.crypto import decrypt_data
        >>> plaintext = decrypt_data(ciphertext, passphrase, salt, nonce)
    """
```

---

### stegvault.vault

Vault data structures and operations.

#### Vault (dataclass)

```python
@dataclass
class Vault:
    """Password vault containing multiple entries.

    Attributes:
        version (str): Vault format version (default: "2.0")
        entries (List[VaultEntry]): List of vault entries
        created (str): Creation timestamp (ISO 8601)
        modified (str): Last modification timestamp
        metadata (dict): Additional metadata
    """

    def add_entry(self, entry: VaultEntry) -> None:
        """Add entry to vault (raises ValueError if key exists)."""

    def get_entry(self, key: str) -> Optional[VaultEntry]:
        """Get entry by key (returns None if not found)."""

    def update_entry(self, key: str, **kwargs) -> bool:
        """Update entry fields (returns False if not found)."""

    def delete_entry(self, key: str) -> bool:
        """Delete entry (returns False if not found)."""

    def has_entry(self, key: str) -> bool:
        """Check if entry exists."""

    def list_keys(self) -> List[str]:
        """Get list of all entry keys."""

    def to_dict(self) -> dict:
        """Convert vault to dictionary."""

    @classmethod
    def from_dict(cls, data: dict) -> "Vault":
        """Create vault from dictionary."""
```

#### VaultEntry (dataclass)

```python
@dataclass
class VaultEntry:
    """Single entry in a password vault.

    Attributes:
        key (str): Unique identifier (e.g., "gmail")
        password (str): The actual password
        username (Optional[str]): Username or email
        url (Optional[str]): Website URL
        notes (Optional[str]): Additional notes
        tags (List[str]): Tags for organization
        totp_secret (Optional[str]): TOTP/2FA secret key
        password_history (List[dict]): Historical passwords (most recent first) **NEW in v0.7.1**
        max_history (int): Maximum history entries to keep (default: 5) **NEW in v0.7.1**
        created (str): Creation timestamp (ISO 8601)
        modified (str): Last modification timestamp
        accessed (Optional[str]): Last access timestamp
    """

    def to_dict(self) -> dict:
        """Convert entry to dictionary."""

    @classmethod
    def from_dict(cls, data: dict) -> "VaultEntry":
        """Create entry from dictionary."""

    def update_modified(self) -> None:
        """Update modified timestamp to now."""

    def update_accessed(self) -> None:
        """Update accessed timestamp to now."""

    def change_password(self, new_password: str, reason: Optional[str] = None) -> None:
        """Change password and add current password to history. **NEW in v0.7.1**

        Args:
            new_password: The new password to set
            reason: Optional reason for password change

        Example:
            >>> entry.change_password("NewSecurePass123", reason="scheduled rotation")
            >>> print(len(entry.password_history))  # 1
        """

    def get_password_history(self) -> List[PasswordHistoryEntry]:
        """Get password history as list of PasswordHistoryEntry objects. **NEW in v0.7.1**

        Returns:
            List of PasswordHistoryEntry objects, most recent first

        Example:
            >>> history = entry.get_password_history()
            >>> for hist in history:
            ...     print(f"{hist.password} - {hist.changed_at}")
        """

    def clear_password_history(self) -> None:
        """Clear all password history. **NEW in v0.7.1**"""
```

#### PasswordHistoryEntry

**NEW in v0.7.1**: Dataclass for tracking password changes.

```python
from stegvault.vault import PasswordHistoryEntry
```

```python
@dataclass
class PasswordHistoryEntry:
    """A historical password entry.

    Attributes:
        password (str): The historical password value
        changed_at (str): Timestamp when password was changed (ISO 8601)
        reason (Optional[str]): Optional reason for change
    """

    password: str
    changed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert history entry to dictionary."""

    @classmethod
    def from_dict(cls, data: dict) -> "PasswordHistoryEntry":
        """Create history entry from dictionary."""
```

---

### stegvault.stego

Steganography operations module (auto-detects PNG/JPEG).

#### embed_payload()

```python
def embed_payload(
    image_path: str,
    payload: bytes,
    seed: int = 0,
    output_path: Optional[str] = None
) -> str:
    """Embed payload in image (auto-detects PNG/JPEG).

    Args:
        image_path: Path to cover image
        payload: Binary payload to embed
        seed: Deprecated parameter (ignored)
        output_path: Optional output path (auto-generated if None)

    Returns:
        Path to output stego image

    Raises:
        CapacityError: If image capacity is insufficient
        StegoError: If embedding fails or format is unsupported

    Example:
        >>> from stegvault.stego import embed_payload
        >>> output = embed_payload("cover.png", payload, output_path="stego.png")
    """
```

#### extract_payload()

```python
def extract_payload(
    image_path: str,
    payload_size: int,
    seed: int = 0
) -> bytes:
    """Extract payload from stego image (auto-detects PNG/JPEG).

    Args:
        image_path: Path to stego image
        payload_size: Size of payload in bytes
        seed: Deprecated parameter (ignored)

    Returns:
        Extracted binary payload

    Raises:
        ExtractionError: If extraction fails
        StegoError: If format is unsupported

    Example:
        >>> from stegvault.stego import extract_payload
        >>> payload = extract_payload("stego.png", 1024)
    """
```

#### calculate_capacity()

```python
def calculate_capacity(
    image: Union[str, PIL.Image.Image]
) -> int:
    """Calculate maximum payload capacity (auto-detects format).

    Args:
        image: Path to image file OR PIL Image object

    Returns:
        Maximum payload size in bytes

    Raises:
        StegoError: If image format is unsupported

    Example:
        >>> from stegvault.stego import calculate_capacity
        >>> capacity = calculate_capacity("image.png")
        >>> print(f"Capacity: {capacity} bytes")
    """
```

---

### stegvault.gallery

Multi-vault management (SQLite-based).

#### Gallery (dataclass)

```python
@dataclass
class Gallery:
    """Gallery for managing multiple vaults.

    Attributes:
        db_path (str): Path to SQLite database
        name (str): Gallery name
        description (str): Gallery description
        created (str): Creation timestamp
    """

    @classmethod
    def init(cls, db_path: str, name: str, description: str = "") -> "Gallery":
        """Initialize new gallery database."""

    @classmethod
    def load(cls, db_path: str) -> "Gallery":
        """Load existing gallery from database."""
```

#### Gallery Operations

```python
def add_vault(
    gallery: Gallery,
    vault_path: str,
    alias: str,
    passphrase: str,
    tags: List[str] = None
) -> None:
    """Add vault to gallery."""

def remove_vault(gallery: Gallery, vault_id: int) -> None:
    """Remove vault from gallery."""

def refresh_vault(gallery: Gallery, vault_id: int, passphrase: str) -> None:
    """Refresh vault cache (after vault modified)."""

def list_vaults(gallery: Gallery) -> List[dict]:
    """List all vaults in gallery."""

def search_entries(
    gallery: Gallery,
    query: Optional[str] = None,
    tag: Optional[str] = None,
    url: Optional[str] = None
) -> List[dict]:
    """Search entries across all vaults."""
```

---

### stegvault.utils

Utility functions.

#### Payload Operations

```python
def serialize_payload(
    salt: bytes,
    nonce: bytes,
    ciphertext: bytes
) -> bytes:
    """Serialize payload components to binary format.

    Format: [Magic:4B][Salt:16B][Nonce:24B][Length:4B][Ciphertext][Tag:16B]

    Returns:
        Serialized payload bytes
    """

def parse_payload(
    payload: bytes
) -> Tuple[bytes, bytes, bytes]:
    """Parse payload to extract components.

    Returns:
        Tuple of (salt, nonce, ciphertext)

    Raises:
        PayloadFormatError: If payload format is invalid
    """

def extract_full_payload(
    image_path: str
) -> bytes:
    """Extract full payload from image (handles magic header, salt derivation).

    Returns:
        Complete payload bytes
    """
```

#### JSON Output (Headless Mode)

```python
def success_json(data: dict) -> dict:
    """Format success response as JSON."""

def error_json(error_type: str, message: str) -> dict:
    """Format error response as JSON."""

def format_vault_entry_json(entry: VaultEntry) -> dict:
    """Format vault entry as JSON."""
```

#### Passphrase Handling

```python
def get_passphrase(
    passphrase: Optional[str] = None,
    passphrase_file: Optional[str] = None,
    allow_prompt: bool = True
) -> str:
    """Get passphrase from multiple sources (priority: explicit > file > env > prompt).

    Args:
        passphrase: Explicit passphrase
        passphrase_file: Path to file containing passphrase
        allow_prompt: Allow interactive prompt if no source

    Returns:
        Passphrase string

    Raises:
        ValueError: If no passphrase source available
    """
```

---

## Error Handling

### Controller Exceptions

Controllers return structured results instead of raising exceptions:

```python
result = controller.load_vault("vault.png", "pass")
if not result.success:
    print(f"Error: {result.error}")
```

### Core Module Exceptions

Core modules raise specific exceptions:

- `ValueError` - Invalid input parameters
- `CapacityError` - Insufficient image capacity
- `ExtractionError` - Steganography extraction failed
- `PayloadFormatError` - Corrupted payload format
- `GalleryDBError` - Gallery database error

---

## See Also

- [Architecture Overview](Architecture-Overview.md) - System architecture
- [Developer Guide](Developer-Guide.md) - Development setup
- [Testing Guide](Testing-Guide.md) - Running tests
