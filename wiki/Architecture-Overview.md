# Architecture Overview

This document provides a technical overview of StegVault's architecture (v0.7.8).

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       StegVault System (v0.7.8)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            User Interface Layer (UI)                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │     CLI     │  │     TUI     │  │     GUI     │      │   │
│  │  │   (Click)   │  │  (Textual)  │  │  (PySide6)  │      │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │   │
│  └─────────┼─────────────────┼─────────────────┼───────────┘   │
│            │                 │                 │               │
│  ┌─────────▼─────────────────▼─────────────────▼───────────┐   │
│  │           Application Layer (Controllers)               │   │
│  │  ┌───────────────────┐  ┌───────────────────┐           │   │
│  │  │ CryptoController  │  │  VaultController  │           │   │
│  │  │                   │  │                   │           │   │
│  │  │ • encrypt()       │  │ • load_vault()    │           │   │
│  │  │ • decrypt()       │  │ • save_vault()    │           │   │
│  │  │ • with_payload()  │  │ • create_new()    │           │   │
│  │  │                   │  │ • CRUD ops        │           │   │
│  │  └─────────┬─────────┘  └─────────┬─────────┘           │   │
│  └────────────┼──────────────────────┼─────────────────────┘   │
│               │                      │                         │
│  ┌────────────▼──────────────────────▼─────────────────────┐   │
│  │                  Core Modules                           │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐   │   │
│  │  │ crypto/ │  │ vault/  │  │ stego/  │  │ gallery/ │   │   │
│  │  │         │  │         │  │         │  │          │   │   │
│  │  │ Argon2id│  │ Vault   │  │ PNG LSB │  │ SQLite   │   │   │
│  │  │ XChaCha │  │ Entry   │  │ JPEG DCT│  │ Search   │   │   │
│  │  │ Poly1305│  │ TOTP    │  │ Dispatch│  │ Metadata │   │   │
│  │  │         │  │ Generator│  │         │  │          │   │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └──────────┘   │   │
│  │                                                          │   │
│  │  ┌───────────────────────────────────────────────────┐  │   │
│  │  │               Utils Module                        │  │   │
│  │  │                                                   │  │   │
│  │  │ • Payload (serialize/parse)                      │  │   │
│  │  │ • Image Format Detection                         │  │   │
│  │  │ • JSON Output (headless mode)                    │  │   │
│  │  │ • Passphrase Handling (file/env/prompt)          │  │   │
│  │  │ • Config Management (TOML)                       │  │   │
│  │  │ • Auto-Updater (PyPI integration)                │  │   │
│  │  │ • Favorite Folders (TUI quick access)            │  │   │
│  │  └───────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│               │              │              │                   │
│  ┌────────────▼──────┐ ┌────▼──────┐ ┌─────▼──────┐            │
│  │     PyNaCl        │ │  Pillow   │ │  jpeglib   │            │
│  │   (libsodium)     │ │   (PIL)   │ │  (DCT)     │            │
│  └───────────────────┘ └───────────┘ └────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Architectural Layers

### 1. User Interface Layer (UI)

Multiple interfaces sharing the same business logic:

- **CLI (Current)**: Click-based command-line interface
- **TUI (Current - v0.7.0)**: Textual-based terminal UI with full keyboard navigation
- **GUI (Planned v0.8.0)**: PySide6-based desktop application

**Benefits**: Users can choose the interface that fits their workflow - terminal purists use TUI, automation uses CLI headless mode, casual users will use GUI.

### 2. Application Layer (v0.6.1)

The **Application Layer** provides UI-agnostic business logic through controllers:

#### CryptoController

High-level encryption/decryption operations:

```python
from stegvault.app.controllers import CryptoController

controller = CryptoController()

# Encrypt
result = controller.encrypt(data, passphrase)
# Returns: EncryptionResult(ciphertext, salt, nonce, success, error)

# Decrypt
result = controller.decrypt(ciphertext, salt, nonce, passphrase)
# Returns: DecryptionResult(plaintext, success, error)
```

**Features**:
- Structured result types (`@dataclass`)
- Optional config injection
- Thread-safe operations
- No UI dependencies

#### VaultController

Complete vault CRUD operations:

```python
from stegvault.app.controllers import VaultController

controller = VaultController()

# Load vault
result = controller.load_vault("vault.png", "pass")
# Returns: VaultLoadResult(vault, success, error)

# Create new vault
vault, success, error = controller.create_new_vault(
    key="gmail", password="secret", username="user@gmail.com"
)

# CRUD operations
vault, success, error = controller.add_vault_entry(vault, ...)
entry_result = controller.get_vault_entry(vault, key)
vault, success, error = controller.update_vault_entry(vault, ...)
vault, success, error = controller.delete_vault_entry(vault, key)

# Save vault
result = controller.save_vault(vault, "output.png", "pass")
# Returns: VaultSaveResult(output_path, success, error)
```

**Benefits**:
- Reusable from any UI (CLI/TUI/GUI)
- Easy to test (no mocking UI frameworks)
- Consistent error handling
- Thread-safe for concurrent access

### 3. Core Modules

#### Cryptography Module (`stegvault/crypto/`)

**Purpose**: Handle all cryptographic operations

**Components**:
- **Key Derivation**: Argon2id with configurable parameters
- **Encryption**: XChaCha20-Poly1305 AEAD cipher
- **Random Generation**: CSPRNG for salts and nonces

**Key Functions**:
```python
def encrypt_data(data: bytes, passphrase: str, ...) -> Tuple[bytes, bytes, bytes]:
    """Encrypt data with passphrase using XChaCha20-Poly1305."""
    # Returns (ciphertext, salt, nonce)

def decrypt_data(ciphertext, salt, nonce, passphrase, ...) -> bytes:
    """Decrypt data with passphrase."""
    # Returns plaintext
```

**Security Features**:
- **Authenticated Encryption**: Poly1305 MAC prevents tampering
- **Memory-Hard KDF**: Argon2id resists GPU/ASIC attacks
- **Fresh Nonces**: New nonce for every encryption

#### Vault Module (`stegvault/vault/`)

**Purpose**: Manage password vault data structures

**Components**:
- `core.py` - Vault and VaultEntry data classes
- `operations.py` - CRUD operations (add, update, delete entries)
- `generator.py` - Cryptographic password generation
- `totp.py` - TOTP/2FA authenticator

**Data Structures**:
```python
@dataclass
class VaultEntry:
    key: str
    password: str
    username: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    totp_secret: Optional[str] = None
    password_history: List[dict] = field(default_factory=list)  # v0.7.1
    created: str  # ISO 8601
    modified: str
    accessed: Optional[str] = None

@dataclass
class Vault:
    version: str = "2.0"
    entries: List[VaultEntry] = field(default_factory=list)
    created: str
    modified: str
    metadata: dict = field(default_factory=dict)
```

#### Steganography Module (`stegvault/stego/`)

**Purpose**: Embed/extract payloads in images

**Components**:
- `png_lsb.py` - PNG LSB steganography (sequential embedding)
- `jpeg_dct.py` - JPEG DCT coefficient modification
- `dispatcher.py` - Automatic format detection and routing

**Key Functions**:
```python
def embed_payload(image_path, payload, seed=0, output_path=None) -> str:
    """Embed payload in image (auto-detects PNG/JPEG)."""

def extract_payload(image_path, payload_size, seed=0) -> bytes:
    """Extract payload from image (auto-detects PNG/JPEG)."""

def calculate_capacity(image) -> int:
    """Calculate max payload capacity (auto-detects format)."""
```

**Techniques**:
- **PNG LSB**: Sequential left-to-right, top-to-bottom bit modification
- **JPEG DCT**: ±1 modification of DCT coefficients (avoids shrinkage)
- **Auto-Detection**: Magic byte detection for format routing

**Capacity**:
- PNG: ~90KB for 400x600 image (lossless)
- JPEG: ~18KB for 400x600 Q85 image (robust to recompression)

#### Gallery Module (`stegvault/gallery/`)

**Purpose**: Multi-vault management

**Components**:
- `core.py` - Gallery data structure
- `db.py` - SQLite database operations
- `operations.py` - Vault management (add, remove, refresh)
- `search.py` - Cross-vault search

**Features**:
- Centralized metadata storage
- Entry caching for fast search
- Tag-based organization
- Cross-vault search

#### Utils Module (`stegvault/utils/`)

**Purpose**: Shared utility functions

**Components**:
- `payload.py` - Payload serialization/parsing
- `image_format.py` - Magic byte detection (PNG/JPEG/GIF/BMP)
- `json_output.py` - JSON formatting for headless mode
- `passphrase.py` - Passphrase from file/env/prompt
- `updater.py` - Auto-update system (v0.7.6-v0.7.8) - PyPI integration, WinError 32 fix, detached updates
- `favorite_folders.py` - Favorite folders manager (v0.7.4) - TUI quick access

## Data Flow

### Backup Flow (Vault Creation)

```
User Input (CLI/TUI/GUI)
    ↓
VaultController.create_new_vault(...)
    ↓
Vault.add_entry() [validation]
    ↓
CryptoController.encrypt_with_payload()
    ↓
crypto.encrypt_data() [Argon2id + XChaCha20]
    ↓
utils.serialize_payload() [format: Magic|Salt|Nonce|Length|Ciphertext|Tag]
    ↓
VaultController.save_vault()
    ↓
stego.embed_payload() [PNG LSB or JPEG DCT]
    ↓
Output stego image
```

### Restore Flow (Vault Loading)

```
Input stego image
    ↓
VaultController.load_vault(image_path, passphrase)
    ↓
stego.extract_payload() [auto-detect PNG/JPEG]
    ↓
utils.parse_payload() [validate magic, extract components]
    ↓
CryptoController.decrypt_from_payload()
    ↓
crypto.decrypt_data() [verify Poly1305 MAC, decrypt]
    ↓
Vault.from_dict() [parse JSON to Vault object]
    ↓
VaultLoadResult(vault, success=True)
```

## Security Boundaries

### Trust Boundaries

1. **User Input → Application**: Validate all inputs (passphrases, file paths, entry data)
2. **Application → Crypto**: Ensure proper parameter types and ranges
3. **Crypto → Stego**: Validate payload size against capacity
4. **Stego → File System**: Safe file operations, temp file cleanup

### Data Validation

- **Before Encryption**: Validate data size, check capacity
- **After Decryption**: Verify magic header, AEAD tag
- **During Entry Operations**: Key uniqueness, required fields

## Error Handling Strategy

### Controller Layer

All controllers return structured results with success/error info:

```python
result = controller.load_vault(image_path, passphrase)
if result.success:
    vault = result.vault
else:
    print(f"Error: {result.error}")  # Human-readable message
```

### Core Layer

Core modules raise specific exceptions:

- `ValueError` - Invalid input parameters
- `CapacityError` - Insufficient image capacity
- `ExtractionError` - Steganography extraction failed
- `PayloadFormatError` - Corrupted payload format

### UI Layer

Each UI handles errors appropriately:

- **CLI**: Exit with error code (1=error, 2=validation)
- **TUI**: Show error dialog
- **GUI**: Show error message box

## Testing Architecture

### Test Coverage (1035 tests, 80%)

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test module interactions
- **Controller Tests**: Test business logic without UI
- **CLI Tests**: Test user-facing commands
- **TUI Tests**: Test terminal UI widgets and screens (v0.7.0+)

### Test Organization

```
tests/unit/
├── test_crypto.py              # Cryptography module
├── test_crypto_controller.py   # CryptoController
├── test_vault.py               # Vault data structures
├── test_vault_controller.py    # VaultController
├── test_stego.py               # PNG LSB steganography
├── test_jpeg_stego.py          # JPEG DCT steganography
├── test_gallery.py             # Gallery management
├── test_json_output.py         # JSON formatting
├── test_passphrase_utils.py    # Passphrase handling
├── test_tui_app.py             # TUI application (v0.7.0+)
├── test_tui_widgets.py         # TUI widgets (v0.7.0+)
├── test_tui_screens.py         # TUI screens (v0.7.0+)
├── test_settings_screen.py     # Settings screen (v0.7.6+)
└── ...
```

## Configuration System

### Config Sources (Priority Order)

1. Explicit command-line arguments (`--arg value`)
2. Configuration file (`~/.stegvault/config.toml`)
3. Default values (hardcoded)

### Config Structure

```toml
[crypto]
argon2_time_cost = 3
argon2_memory_cost = 65536
argon2_parallelism = 4

[cli]
verbose = false
progress_bars = true

[stego]
default_seed = 12345

[vault]
default_tags = ["personal"]

[updates]  # v0.7.6
auto_check = true
auto_upgrade = false
check_interval = 86400  # 24 hours
```

## Extensibility Points

### Adding New Steganography Methods

1. Create new module in `stegvault/stego/`
2. Implement `embed_payload()`, `extract_payload()`, `calculate_capacity()`
3. Update `dispatcher.py` to route new format

### Adding New UI

1. Create new package (e.g., `stegvault/tui/`)
2. Import controllers from `stegvault/app/controllers/`
3. Handle controller results and display to user

### Adding New Controllers

1. Create controller in `stegvault/app/controllers/`
2. Define result dataclasses
3. Implement methods with structured returns
4. Write comprehensive tests

## Performance Considerations

### Argon2id Parameters

- **Time Cost**: 3 iterations (default) - ~100ms on modern CPU
- **Memory Cost**: 64MB (default) - resistant to GPU attacks
- **Parallelism**: 4 threads (default) - utilize multi-core CPUs

### Capacity Calculations

- **PNG**: O(1) - width × height × channels / 8
- **JPEG**: O(n) - iterate DCT blocks, count coefficients |value| > 1

### Gallery Search

- **Entry Cache**: SQLite FTS (Full-Text Search) for instant results
- **Metadata**: Indexed by vault_id, key, tags
- **Auto-Refresh**: Only when vault modified timestamp changes

## Future Architecture (Roadmap)

### v0.7.0: TUI (Textual) - ✅ COMPLETED

- ✅ Added `stegvault/tui/` package
- ✅ Reused `VaultController` and `CryptoController`
- ✅ Implemented reactive UI with Textual widgets
- ✅ Full keyboard navigation
- ✅ Live search and filtering
- ✅ TOTP auto-refresh
- ✅ Password generator integration
- ✅ Favorite folders (v0.7.4)
- ✅ Password history viewer (v0.7.1)
- ✅ Auto-update system with Settings screen (v0.7.6)

### v0.8.0: GUI (PySide6) - 🔜 PLANNED

- Add `stegvault/gui/` package
- Thread-safe controller usage (QThread)
- Native desktop application

### v0.9.0: Cloud Sync (Optional)

- End-to-end encrypted cloud backup
- Conflict resolution
- Multi-device support

## See Also

- [Developer Guide](Developer-Guide.md) - Setting up development environment
- [API Reference](API-Reference.md) - Complete API documentation
- [Testing Guide](Testing-Guide.md) - Running and writing tests
- [Security Model](Security-Model.md) - Security assumptions and guarantees
