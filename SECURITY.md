# Security Policy

## Overview

StegVault is a security-critical application that handles sensitive user credentials. We take security vulnerabilities very seriously and appreciate responsible disclosure from the security community.

**IMPORTANT**: This software is currently in development and has **NOT yet undergone a professional security audit**. Use at your own risk for production systems.

## Supported Versions

Security updates are provided for the following versions:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 1.0.x   | :white_check_mark: | Development (pre-release) |
| < 1.0   | :x:                | Experimental/alpha |

**Note**: Until version 1.0.0 is released, breaking changes may occur as security improvements are implemented.

## Reporting a Vulnerability

**DO NOT** open public GitHub issues for security vulnerabilities.

### Reporting Process

To report a security vulnerability, please use **one** of the following methods:

#### 1. GitHub Security Advisories (Preferred)
- Navigate to the [Security tab](../../security/advisories)
- Click "Report a vulnerability"
- Fill out the private advisory form

#### 2. Email (Alternative)
- Email: [StegVault@proton.me]
- Subject: `[SECURITY] StegVault Vulnerability Report`
- Include:
  - Vulnerability description
  - Steps to reproduce
  - Affected versions
  - Potential impact assessment
  - Suggested fix (if available)

#### 3. Encrypted Communication
For highly sensitive disclosures:
- PGP Key: `38027F466AF1A48FD95C175C127BD97B6B1D7CA8`
- Public key available at: `https://github.com/kalashnikxvxiii.gpg`

### What to Include

Please provide as much detail as possible:

1. **Vulnerability Type**
   - Cryptographic weakness
   - Authentication bypass
   - Data leakage
   - Implementation flaw
   - Dependency vulnerability
   - Other (describe)

2. **Affected Components**
   - Encryption (crypto module)
   - Steganography (stego module)
   - Key derivation
   - Payload handling
   - CLI interface
   - Dependencies

3. **Attack Scenario**
   - Required attacker capabilities
   - Attack complexity
   - Prerequisites
   - Step-by-step reproduction

4. **Impact Assessment**
   - Confidentiality impact
   - Integrity impact
   - Availability impact
   - Estimated severity (Low/Medium/High/Critical)

### Response Timeline

We are committed to responding promptly:

- **Initial Response**: Within 48 hours of receipt
- **Status Update**: Within 7 days (confirm/deny vulnerability)
- **Fix Timeline**:
  - Critical: 7-14 days
  - High: 14-30 days
  - Medium: 30-60 days
  - Low: Next planned release

### Disclosure Policy

We follow **coordinated disclosure**:

1. **Day 0**: Vulnerability reported privately
2. **Day 1-2**: Initial acknowledgment sent
3. **Day 2-7**: Validation and severity assessment
4. **Day 7-30**: Fix development and testing
5. **Day 30**: Public disclosure (if fix available)
6. **Day 90**: Public disclosure (even if no fix available)

We will:
- Credit reporters in security advisories (unless anonymity requested)
- Publish CVE identifiers for verified vulnerabilities
- Release security patches with detailed changelogs
- Notify users via GitHub Security Advisories

## Security Best Practices for Users

### Critical Requirements

1. **Strong Passphrase**
   - Minimum 16 characters
   - Include uppercase, lowercase, numbers, symbols
   - Use passphrase generator or diceware
   - **NEVER** reuse passphrases from other services

2. **Backup Strategy**
   - Store stego images in multiple secure locations
   - Keep offline backups (USB drive, encrypted external storage)
   - Test restoration process regularly
   - **Losing image OR passphrase = permanent data loss**

3. **Image Format**
   - **ALWAYS use PNG** (lossless format)
   - **AVOID JPEG** (lossy compression destroys payload)
   - Do not edit/resize images after embedding
   - Verify backup integrity after creation

4. **Operational Security**
   - Run on trusted, malware-free systems
   - Use full-disk encryption on devices storing stego images
   - Clear clipboard after copying passwords
   - Secure delete original cover images if sensitive

### Advanced Security

- **Verify Integrity**: Check AEAD tag validation succeeds
- **Monitor Dependencies**: Keep Python and libraries updated
- **Audit Mode**: Review source code before use
- **Airgap Option**: Run on offline system for maximum security

## Known Limitations & Threat Model

### What StegVault Protects Against

:white_check_mark: **Passive observation of image file**
- Encrypted payload prevents plaintext recovery
- Argon2id KDF resists brute-force attacks

:white_check_mark: **Image interception in transit**
- AEAD authentication detects tampering
- Strong encryption ensures confidentiality

:white_check_mark: **Weak password attacks**
- Memory-hard KDF (64MB Argon2id) slows GPU/ASIC attacks

### What StegVault Does NOT Protect Against

:x: **Advanced steganalysis**
- LSB embedding detectable by statistical analysis
- Not suitable for high-risk environments requiring deniability

:x: **Compromised system**
- Keyloggers can capture passphrase during entry
- Malware can extract plaintext from memory
- Use dedicated secure system for sensitive operations

:x: **Image format conversion**
- JPEG compression destroys payload
- Format conversion may corrupt data

:x: **Quantum computing attacks**
- XChaCha20 uses 256-bit keys (vulnerable to Grover's algorithm)
- Upgrade to post-quantum crypto planned for future versions

:x: **Offline brute-force with powerful hardware**
- Attacker with image can attempt dictionary/brute-force
- Mitigated (not eliminated) by Argon2id parameters

:x: **Magic header identification**
- Payload contains "SPW1" identifier
- Trivial detection if attacker extracts LSBs

### Threat Model Summary

**Assumed Attacker Capabilities**:
- Has copy of stego image
- Knows StegVault is being used
- Has access to extraction algorithm
- Limited computational resources (< 1000 GPU-years)

**Out of Scope**:
- Nation-state level attacks
- Physical device tampering
- Side-channel attacks (timing, power analysis)
- Social engineering attacks

## Cryptographic Implementation

### Algorithms & Parameters

| Component | Algorithm | Parameters | Library |
|-----------|-----------|------------|---------|
| **AEAD** | XChaCha20-Poly1305 | 256-bit key, 192-bit nonce | PyNaCl (libsodium) |
| **KDF** | Argon2id | 3 iterations, 64MB RAM, 4 threads | argon2-cffi |
| **CSPRNG** | OS-provided | /dev/urandom (Linux), CryptGenRandom (Windows) | `secrets` module |

### Security Rationale

- **XChaCha20-Poly1305**: Modern AEAD cipher, no known practical attacks
- **Argon2id**: Winner of Password Hashing Competition 2015, resistant to side-channel and GPU attacks
- **Large Nonce (192-bit)**: Eliminates collision probability for random nonces
- **Strong PRNG**: Cryptographically secure randomness for salts/nonces

### Dependencies

All cryptographic operations rely on:
- **libsodium** (via PyNaCl) - Audited crypto library
- **argon2-cffi** - Official Argon2 bindings

**Dependency Security**:
- Monitor CVE databases for vulnerabilities
- Automated dependency scanning via GitHub Dependabot
- Pin minimum secure versions in `requirements.txt`

## Security Development Lifecycle

### Current Status

- [x] Secure design review
- [x] Automated testing (63+ unit tests)
- [x] Static analysis (bandit, mypy)
- [x] Dependency scanning
- [ ] **External security audit (pending)**
- [ ] Fuzzing (planned)
- [ ] Penetration testing (planned)

### Pre-Release Security Checklist

Before v1.0.0 release:
- [ ] Professional security audit by third-party
- [ ] Cryptographic implementation review
- [ ] Fuzz testing payload parser
- [ ] Side-channel analysis
- [ ] Dependency audit
- [ ] Documentation review

## Secure Development Practices

Contributors must follow these practices:

1. **Code Review**: All security-sensitive code requires 2+ reviewer approvals
2. **Testing**: Security fixes must include regression tests
3. **Dependencies**: Justify all new crypto/security dependencies
4. **Secrets**: Never commit keys, passwords, or sensitive test data
5. **Compliance**: Follow OWASP secure coding guidelines

## Vulnerability Disclosure History

*No vulnerabilities disclosed yet (pre-release software)*

Once released, this section will contain:
- CVE identifiers
- Severity ratings
- Affected versions
- Mitigation steps
- Fix versions

## Security Contact

- **E-Mail**: StegVault@proton.me
- **Response Time**: 48 hours
- **PGP Key**: 38027F466AF1A48FD95C175C127BD97B6B1D7CA8
- **GitHub Security**: Use Security Advisories feature

---

**Last Updated**: 2025-11-11

**Next Review**: Before v1.0.0 release (or every 6 months)

## Legal

Security researchers acting in good faith will not face legal action for:
- Testing on their own systems/data
- Following responsible disclosure procedures
- Not accessing/exfiltrating others' data
- Not performing destructive actions

We are committed to working with the security community to keep StegVault users safe.