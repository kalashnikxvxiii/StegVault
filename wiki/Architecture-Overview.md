# Architecture Overview

This document provides a technical overview of StegVault's architecture.

## System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      StegVault System                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐                                          │
│  │   CLI Layer  │  ← User Interface (Click framework)      │
│  └──────┬───────┘                                          │
│         │                                                  │
│  ┌──────▼───────────────────────────────────────┐          │
│  │          StegVault Core API                  │          │
│  ├──────────────────────────────────────────────┤          │
│  │                                              │          │
│  │  ┌─────────────┐  ┌─────────────┐            │          │
│  │  │   Crypto    │  │    Stego    │            │          │
│  │  │   Module    │  │   Module    │            │          │
│  │  │             │  │             │            │          │
│  │  │ • Argon2id  │  │ • LSB PNG   │            │          │
│  │  │ • XChaCha20 │  │ • Pseudo-   │            │          │
│  │  │ • Poly1305  │  │   random    │            │          │
│  │  │             │  │   ordering  │            │          │
│  │  └─────────────┘  └─────────────┘            │          │
│  │                                              │          │
│  │  ┌──────────────────────────────┐            │          │
│  │  │      Utils Module            │            │          │
│  │  │                              │            │          │
│  │  │ • Payload serialization      │            │          │
│  │  │ • Format parsing             │            │          │
│  │  │ • Capacity validation        │            │          │
│  │  └──────────────────────────────┘            │          │
│  │                                              │          │
│  └──────────────────────────────────────────────┘          │
│         │              │             │                     │
│  ┌──────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐              │
│  │   PyNaCl    │ │  Pillow  │ │   argon2    │              │
│  │ (libsodium) │ │  (PIL)   │ │   -cffi     │              │
│  └─────────────┘ └──────────┘ └─────────────┘              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. Cryptography Module (`stegvault/crypto/`)

**Purpose**: Handle all cryptographic operations

**Components**:
- **Key Derivation**: Argon2id with configurable parameters
- **Encryption**: XChaCha20-Poly1305 AEAD cipher
- **Random Generation**: CSPRNG for salts and nonces

**Key Functions**:
```python
def encrypt_data(plaintext: bytes, passphrase: str) -> Tuple[bytes, bytes, bytes]
def decrypt_data(ciphertext: bytes, salt: bytes, nonce: bytes, passphrase: str) -> bytes
def derive_key(passphrase: str, salt: bytes) -> bytes
```

**Security Properties**:
- Argon2id parameters: 3 iterations, 64MB memory, 4 threads
- 256-bit keys for XChaCha20
- 192-bit nonces (extended compared to ChaCha20)
- 128-bit Poly1305 authentication tags

### 2. Steganography Module (`stegvault/stego/`)

**Purpose**: Embed and extract payloads in images

**Components**:
- **LSB Embedding**: Modify least significant bits of pixels
- **Pixel Ordering**: Pseudo-random sequence generation
- **Capacity Calculation**: Determine available space

**Key Functions**:
```python
def embed_payload(image_path: str, payload: bytes, seed: int, output_path: str) -> Image
def extract_payload(image_path: str, payload_size: int, seed: int) -> bytes
def calculate_capacity(image: Image) -> int
```

**Steganography Details**:
- Uses LSB of R, G, B channels
- Capacity: `(width * height * 3) / 8` bytes
- Seed derived from salt for reproducibility
- Supports RGB and RGBA images

### 3. Utils Module (`stegvault/utils/`)

**Purpose**: Payload format handling and validation

**Components**:
- **Serialization**: Convert components to binary format
- **Parsing**: Extract components from binary payload
- **Validation**: Check capacity and format integrity

**Payload Structure**:
```python
class PayloadFormat:
    magic: bytes     # 4 bytes: "SPW1"
    salt: bytes      # 16 bytes
    nonce: bytes     # 24 bytes
    ciphertext: bytes  # Variable length (includes 16-byte tag)
```

### 4. CLI Module (`stegvault/cli.py`)

**Purpose**: User interface for StegVault operations

**Commands**:
- `backup`: Create encrypted backup in image
- `restore`: Recover password from image
- `check`: Verify image capacity

## Data Flow

### Backup Creation Flow

```
User Input
   ├─ Master Password
   ├─ Passphrase
   └─ Cover Image
       │
       ▼
┌──────────────────┐
│ 1. Validation    │
│  • Check image   │
│  • Verify pass   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 2. Encryption    │
│  • Gen salt      │──┐
│  • Gen nonce     │  │ CSPRNG
│  • Derive key    │◄─┘ (os.urandom)
│  • Encrypt data  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 3. Serialization │
│  • Add magic     │
│  • Combine parts │
│  • Create payload│
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 4. Embedding     │
│  • Seed from salt│
│  • Shuffle pixels│
│  • Modify LSBs   │
└────────┬─────────┘
         ▼
   Stego Image
```

### Password Recovery Flow

```
Stego Image + Passphrase
       │
       ▼
┌──────────────────┐
│ 1. Extraction    │
│  • Read header   │
│  • Get CT length │
│  • Extract full  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 2. Parsing       │
│  • Verify magic  │
│  • Extract salt  │
│  • Extract nonce │
│  • Extract CT    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 3. Re-extraction │
│  • Seed from salt│
│  • Correct order │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 4. Decryption    │
│  • Derive key    │
│  • Decrypt       │
│  • Verify tag    │
└────────┬─────────┘
         ▼
   Master Password
```

## Security Architecture

### Defense in Depth

1. **Cryptographic Layer**
   - Strong encryption (XChaCha20-Poly1305)
   - Robust KDF (Argon2id)
   - Authentication tags (AEAD)

2. **Steganographic Layer**
   - Invisible storage (LSB modification)
   - Pseudo-random ordering (detection resistance)
   - Minimal statistical signature

3. **Format Layer**
   - Versioned payload (forward compatibility)
   - Integrity checks (length validation)
   - Magic header (corruption detection)

### Trust Boundaries

```
┌─────────────────────────────────────────┐
│         Trusted Environment             │
│  ┌─────────────────────────────────┐    │
│  │    StegVault Process            │    │
│  │  • Encryption                   │    │
│  │  • Decryption                   │    │
│  │  • Key derivation               │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Secrets exist only in memory           │
└─────────────────────────────────────────┘
                  │
                  │ Encrypted payload only
                  ▼
┌─────────────────────────────────────────┐
│       Untrusted Environment             │
│  • File system                          │
│  • Network                              │
│  • Cloud storage                        │
│  • External media                       │
│                                         │
│  Only encrypted data exposed            │
└─────────────────────────────────────────┘
```

## Performance Characteristics

### Computational Costs

| Operation | Primary Cost | Time (typical) |
|-----------|--------------|----------------|
| **Key Derivation** | Argon2id (64MB) | ~200-500ms |
| **Encryption** | XChaCha20 | <10ms |
| **Decryption** | XChaCha20 | <10ms |
| **LSB Embed** | Image processing | 50-200ms |
| **LSB Extract** | Image processing | 50-200ms |

### Memory Requirements

| Component | Memory Usage |
|-----------|--------------|
| Argon2id | 64MB (configurable) |
| Image buffer | Width × Height × 3-4 bytes |
| Payload | Actual data size |
| Total (typical) | ~100-200MB for large images |

### Scalability

**Image Size Impact**:
- Small (100×100): ~10ms embedding
- Medium (500×500): ~50ms embedding
- Large (2000×2000): ~200ms embedding

**Password Length Impact**:
- Minimal (encryption is fast)
- Linear with payload size for serialization

## Error Handling

### Error Hierarchy

```
Exception
├─ CryptoError
│  ├─ DecryptionError
│  └─ KeyDerivationError
├─ StegoError
│  ├─ CapacityError
│  └─ ExtractionError
└─ PayloadError
   └─ PayloadFormatError
```

### Error Recovery

| Error Type | Recovery Strategy |
|------------|-------------------|
| **Wrong Passphrase** | Prompt user to retry |
| **Capacity Exceeded** | Suggest larger image |
| **Corrupted Image** | Check file integrity, try backup |
| **Format Error** | Incompatible version or corruption |

## Testing Architecture

### Test Pyramid

```
        ┌────────────┐
        │    E2E     │  ← Roundtrip tests
        │   Tests    │    (backup → restore)
        └────────────┘
              │
        ┌─────▼──────┐
        │Integration │  ← Module interaction
        │   Tests    │
        └─────┬──────┘
              │
        ┌─────▼──────┐
        │    Unit    │  ← Individual functions
        │   Tests    │    (63+ tests)
        └────────────┘
```

### Test Coverage

- **Crypto Module**: 26 tests, 90% coverage
- **Payload Module**: 22 tests, 100% coverage
- **Stego Module**: 15 tests, 90% coverage

## Extensibility Points

### Plugin Architecture (Future)

Potential extension points:
1. **Stego Algorithms**: Support JPEG DCT, audio, video
2. **Crypto Algorithms**: Post-quantum alternatives
3. **Storage Backends**: Cloud providers, databases
4. **UI Frontends**: GUI, web interface, mobile apps

### Configuration

Future configuration system:
```python
# ~/.stegvault/config.toml
[crypto]
argon2_time_cost = 3
argon2_memory_cost = 65536
argon2_parallelism = 4

[stego]
default_algorithm = "lsb_png"
embedding_strategy = "pseudo_random"

[cli]
default_output_format = "png"
verbose = false
```

## Development Guidelines

### Adding New Features

1. **Design Phase**
   - Document security implications
   - Plan backward compatibility

2. **Implementation Phase**
   - Write tests first (TDD)
   - Implement feature
   - Document in docstrings

3. **Review Phase**
   - Security review for crypto changes
   - Code review by maintainers
   - Update CHANGELOG.md

### Code Organization

```
stegvault/
├── __init__.py          # Public API
├── crypto/
│   ├── __init__.py      # Exports
│   └── core.py          # Implementation
├── stego/
│   ├── __init__.py
│   └── png_lsb.py       # LSB implementation
├── utils/
│   ├── __init__.py
│   └── payload.py       # Format handling
└── cli.py               # CLI interface
```

## Future Architecture Considerations

### Planned Enhancements

1. **Modular Stego**: Plugin system for algorithms
2. **Hardware Acceleration**: GPU for Argon2id
3. **Distributed Storage**: Shard across multiple images
4. **Mobile Support**: Native iOS/Android libraries

### Scalability Plans

- Batch processing for multiple passwords
- Asynchronous operations for GUI
- Streaming for large images
- Incremental backup updates

---

For implementation details, see:
- [Cryptography Details](Cryptography-Details.md)
- [Steganography Techniques](Steganography-Techniques.md)
- [Payload Format Specification](Payload-Format-Specification.md)
