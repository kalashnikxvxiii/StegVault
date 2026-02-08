# Security Model

StegVault's security architecture and design principles.

## Security Objectives

### Primary Goals

1. **Confidentiality**: Password remains secret even if backup image is captured
2. **Integrity**: Tampering is detected via authentication tags
3. **Availability**: Legitimate user can recover password with correct passphrase

### Non-Goals

- **Steganography invisibility**: LSB embedding is detectable by experts
- **Post-quantum security**: Current algorithms vulnerable to quantum computers
- **Side-channel protection**: Memory dumps may reveal plaintext temporarily

## Threat Model

See [Threat Model](Threat-Model.md) for detailed threat analysis.

### Assumed Attackers

**Passive Attacker**:
- Has access to stego image
- Cannot modify image
- Performs offline analysis

**Active Attacker**:
- Can modify stored images
- Cannot access user's passphrase
- May attempt tampering

### Out of Scope

- Attackers with physical access to running system
- Keyloggers capturing passphrase entry
- Coercion/rubber-hose attacks

## Security Layers

### Layer 1: Encryption

**Algorithm**: XChaCha20-Poly1305 AEAD

**Properties**:
- 256-bit key strength
- Authenticated encryption (detects tampering)
- Random 192-bit nonce (prevents reuse)

**Protection**: Even if attacker knows payload location, cannot decrypt without passphrase.

### Layer 2: Key Derivation

**Algorithm**: Argon2id

**Parameters**:
- Time cost: 3 iterations
- Memory: 64 MB
- Parallelism: 4 threads

**Protection**: Brute-force attacks are expensive (100ms per guess).

### Layer 3: Steganography

**Algorithm**: LSB with pseudo-random ordering

**Protection**: Payload presence is obscured (not cryptographically hidden).

## Cryptographic Primitives

### XChaCha20-Poly1305

**Status**: Modern, well-vetted AEAD cipher

**Properties**:
- IND-CPA secure (indistinguishable ciphertexts)
- INT-CTXT secure (integrity)
- No known practical attacks

**Limitations**: Not post-quantum secure

### Argon2id

**Status**: Winner of Password Hashing Competition

**Properties**:
- Memory-hard (resistant to GPU attacks)
- Side-channel resistant (hybrid of Argon2i/d)
- Configurable cost parameters

**Limitations**: Tunable parameters affect security/performance trade-off

## Attack Resistance

### Brute Force Attacks

**Scenario**: Attacker has stego image, tries all passphrases

**Defense**:
- Argon2id makes each guess expensive (~100ms)
- Strong passphrase (16+ chars) = infeasible search space

**Attack Cost** (16-char random passphrase):
```
Entropy: ~95 bits
Guesses: 2^95
Time per guess: 100ms
Total time: 10^21 years (single CPU)
```

**Conclusion**: Strong passphrase makes brute force infeasible.

### Dictionary Attacks

**Scenario**: Attacker tries common passwords/phrases

**Defense**:
- Argon2id slows down each attempt
- Salt prevents rainbow tables

**Mitigation**: Use non-dictionary passphrases.

### Tampering Attacks

**Scenario**: Attacker modifies ciphertext in image

**Defense**:
- Poly1305 MAC authenticates ciphertext
- Any modification causes decryption failure

**Protection**: Tampering is reliably detected.

### Steganalysis

**Scenario**: Attacker detects steganography presence

**Reality**:
- LSB embedding IS detectable by statistical analysis
- Pseudo-random ordering helps, but not foolproof

**Defense**: Steganography is obscurity layer, NOT security layer.

## Security Properties

### What StegVault Guarantees

✅ **Confidentiality**: Password encrypted with strong AEAD
✅ **Integrity**: Tampering detected via authentication
✅ **Uniqueness**: Each backup uses unique salt/nonce
✅ **Forward secrecy**: Compromise of one backup doesn't affect others

### What StegVault Does NOT Guarantee

❌ **Steganography undetectability**: LSB can be found
❌ **Metadata hiding**: Payload format reveals usage
❌ **Post-quantum security**: Quantum computers can break XChaCha20
❌ **Physical security**: Best-effort mitigation only—decrypted buffers are wiped with `secure_wipe()` (see Threat Model T6); memory dumps may still expose copies in interpreter/C extensions

## Key Management

### Passphrase Storage

**User responsibility**: StegVault NEVER stores passphrases.

**Options**:
- Memorize strong passphrase
- Store in separate password manager
- Physical backup (secure location)

### Key Derivation

```
User Passphrase
       ↓
   Argon2id (with random salt)
       ↓
  256-bit Encryption Key
       ↓
 XChaCha20-Poly1305 (with random nonce)
       ↓
   Ciphertext
```

**Security**: Unique salt per backup prevents key reuse.

## Payload Security

### Encrypted Payload

```
[Magic][Salt][Nonce][Length][Ciphertext][Tag]
  ↑      ↑     ↑       ↑          ↑       ↑
Public Public Public Public  ENCRYPTED   MAC
```

**Only ciphertext is secret**. All other fields are public by design.

### Information Leakage

**What an attacker learns**:
- StegVault is being used (magic header)
- Approximate password length (ciphertext length)
- Algorithm version (SPW1)

**What remains secret**:
- Actual password content
- Encryption passphrase

## Trust Model

### What You Must Trust

1. **Cryptographic libraries**:
   - libsodium (PyNaCl)
   - Argon2 reference implementation

2. **Python runtime**: No backdoors in Python interpreter

3. **Operating system**: CSPRNG is truly random

4. **Your device**: No malware/keyloggers present

### What You Don't Need to Trust

- Cloud storage providers (backup is encrypted)
- Image hosting services (cannot decrypt)
- StegVault developers (open source, auditable)

## Operational Security

### User Responsibilities

**Critical**:
- Choose strong passphrases (16+ characters)
- Protect passphrases (memorize or secure storage)
- Keep multiple backup copies
- Test recovery periodically

**Recommended**:
- Use PNG format (avoid JPEG)
- Don't share cover images publicly
- Store backups in multiple secure locations

### System Security

**Environment**:
- Run on trusted device
- Keep system updated
- Use antivirus/antimalware
- Avoid shared/public computers

## Security Audits

### Current Status

**Version 0.6.1**: No external security audit yet

**Code Quality**:
- 614 tests (100% pass rate)
- 92% code coverage
- Continuous Integration (Python 3.9-3.14)
- Security scanning (CodeQL, Bandit)

**Future Plans**:
- External cryptographic review
- Penetration testing
- Bug bounty program

### Self-Assessment

**Strengths**:
- Uses well-vetted crypto primitives
- Simple, auditable codebase
- No custom crypto implementations

**Areas for Improvement**:
- Post-quantum cryptography
- More robust steganography
- Side-channel hardening

## Vulnerability Disclosure

See [Vulnerability Disclosure](Vulnerability-Disclosure.md) for reporting security issues.

## Compliance

### Standards Followed

- NIST recommendations for symmetric encryption
- OWASP cryptographic storage guidelines
- Python security best practices

### Certifications

None currently. Open source project, not certified.

## Limitations

See [Known Limitations](Known-Limitations.md) for detailed discussion.

**Key limitations**:
- Steganography is detectable
- Weak passphrases remain vulnerable
- No protection against quantum computers

## Recommendations

### For Users

1. Use passphrases with 16+ random characters
2. Store backups in multiple secure locations
3. Test recovery regularly
4. Never share backup images publicly

### For Developers

1. Keep crypto libraries updated
2. Follow secure coding practices
3. Report security issues responsibly
4. Contribute to security reviews

## Next Steps

- Read [Threat Model](Threat-Model.md)
- Review [Known Limitations](Known-Limitations.md)
- Check [Security Best Practices](Security-Best-Practices.md)
- See [Vulnerability Disclosure](Vulnerability-Disclosure.md)
