# Threat Model

Analysis of threats against StegVault and their mitigations.

## Attacker Profiles

### Passive Observer

**Capabilities**:
- Accesses backup image (cloud storage, USB find, etc.)
- Can analyze image with tools
- Cannot modify image or system

**Goals**:
- Recover password from backup
- Detect steganography usage

**Likelihood**: High (most common scenario)

### Active Attacker

**Capabilities**:
- Modifies backup images
- Replaces backups with tampered versions
- Cannot capture passphrase

**Goals**:
- Inject malicious payloads
- Cause denial of service

**Likelihood**: Medium

### Privileged Attacker

**Capabilities**:
- System-level access
- Memory dumps
- Keylogging

**Goals**:
- Capture passphrase during entry
- Extract password from RAM

**Likelihood**: Low (requires compromised system)

### Quantum Attacker (Future)

**Capabilities**:
- Large-scale quantum computer
- Can break XChaCha20 encryption

**Goals**:
- Decrypt archived backups

**Likelihood**: Very Low (not yet practical)

## Threat Scenarios

### T1: Brute Force Attack

**Scenario**: Attacker has backup, tries all passphrases

**Attack Steps**:
1. Extract payload from image
2. Parse salt and nonce
3. For each candidate passphrase:
   - Derive key using Argon2id
   - Attempt decryption
   - Check if authentication passes

**Mitigations**:
- Argon2id slows each attempt (~100ms)
- Strong passphrase increases search space
- No offline shortcuts (unique salt prevents rainbow tables)

**Residual Risk**: Weak passphrases remain vulnerable

**Severity**: High | **Exploitability**: Medium | **Impact**: Critical

---

### T2: Dictionary Attack

**Scenario**: Attacker tries common passwords

**Attack Steps**:
1. Build dictionary (common passwords, names, dates)
2. Try each dictionary entry
3. Use password mangling rules

**Mitigations**:
- Passphrase strength checker warns users
- Argon2id makes each guess expensive
- Documentation emphasizes strong passphrases

**Residual Risk**: Users may ignore warnings

**Severity**: High | **Exploitability**: Medium | **Impact**: Critical

---

### T3: Steganalysis Detection

**Scenario**: Attacker detects steganography presence

**Attack Steps**:
1. Analyze LSB distribution
2. Run chi-square test
3. Use RS steganalysis
4. Identify non-random LSB patterns

**Mitigations**:
- Pseudo-random pixel ordering
- Encryption before embedding (no plaintext patterns)
- Documentation: steganography is NOT the security layer

**Residual Risk**: LSB embedding IS detectable

**Severity**: Low | **Exploitability**: Easy | **Impact**: Low
(Detection alone doesn't compromise password)

---

### T4: Ciphertext Tampering

**Scenario**: Attacker modifies encrypted payload

**Attack Steps**:
1. Modify bits in stego image
2. User attempts to restore
3. Goal: Cause crash or inject malicious data

**Mitigations**:
- AEAD tag detects any modification
- Decryption fails if tag doesn't verify
- No unauthenticated decryption

**Residual Risk**: None (reliably detected)

**Severity**: Medium | **Exploitability**: Easy | **Impact**: None
(Tampering detected, attack fails)

---

### T5: Passphrase Capture

**Scenario**: Keylogger captures passphrase during entry

**Attack Steps**:
1. Install keylogger/malware
2. Wait for user to restore backup
3. Capture passphrase
4. Use passphrase to decrypt backup

**Mitigations**:
- **Out of scope** for StegVault
- User responsibility: keep system clean
- Documentation warns about keyloggers

**Residual Risk**: High if system compromised

**Severity**: Critical | **Exploitability**: Hard | **Impact**: Critical

---

### T6: Memory Dump Attack

**Scenario**: Attacker dumps RAM after password recovery

**Attack Steps**:
1. Trigger password recovery
2. Dump process memory
3. Search for plaintext password in dump

**Mitigations**:
- **Implemented**: Decrypted plaintext is returned as mutable bytearray; callers use
  `secure_wipe()` after use to overwrite buffers (see `stegvault.utils.secure_memory`).
- VaultController, CLI, batch, and gallery paths wipe decrypted buffers in try/finally.

**Residual Risk**: Low (best-effort; Python cannot guarantee no copies elsewhere)

**Severity**: Medium | **Exploitability**: Hard | **Impact**: High

---

### T7: Weak Random Number Generation

**Scenario**: PRNG is predictable

**Attack Steps**:
1. If RNG predictable, salts/nonces may repeat
2. Nonce reuse breaks encryption security
3. Attacker recovers keys

**Mitigations**:
- Use OS-provided CSPRNG (via libsodium)
- No custom RNG implementations
- Well-tested libraries (PyNaCl)

**Residual Risk**: Very Low (trust OS/libsodium)

**Severity**: Critical | **Exploitability**: Very Hard | **Impact**: Critical

---

### T8: JPEG Recompression

**Scenario**: User saves backup as JPEG, later re-saves

**Attack Steps**:
1. User creates backup in JPEG
2. Image edited or recompressed
3. LSBs change, payload corrupted
4. Recovery fails

**Mitigations**:
- Documentation strongly recommends PNG
- CLI warns when using JPEG
- Format validation on extraction

**Residual Risk**: Medium (user may ignore warnings)

**Severity**: Medium | **Exploitability**: Easy | **Impact**: High
(Backup destroyed)

---

### T9: Side-Channel Timing Attacks

**Scenario**: Attacker measures decryption timing

**Attack Steps**:
1. Submit many forged payloads
2. Measure time to reject each
3. Extract information about key via timing differences

**Mitigations**:
- libsodium uses constant-time operations
- Argon2id resistant to timing attacks
- AEAD verification is constant-time

**Residual Risk**: Very Low (libraries designed for this)

**Severity**: Low | **Exploitability**: Very Hard | **Impact**: Medium

---

### T10: Supply Chain Attack

**Scenario**: Malicious code in dependencies

**Attack Steps**:
1. Compromise upstream library (PyNaCl, Pillow, etc.)
2. Inject backdoor
3. Steal passphrases or passwords

**Mitigations**:
- Use well-maintained, audited libraries
- Pin dependency versions
- Monitor security advisories

**Residual Risk**: Low but non-zero

**Severity**: Critical | **Exploitability**: Very Hard | **Impact**: Critical

---

## Threat Matrix

| Threat | Severity | Exploitability | Mitigation | Residual Risk |
|--------|----------|----------------|------------|---------------|
| T1: Brute Force | High | Medium | Argon2id + strong passphrase | Medium |
| T2: Dictionary | High | Medium | Passphrase checker | Medium |
| T3: Steganalysis | Low | Easy | Encryption layer | Low |
| T4: Tampering | Medium | Easy | AEAD authentication | None |
| T5: Keylogger | Critical | Hard | Out of scope | High |
| T6: Memory Dump | Medium | Hard | Memory clearing (secure_wipe) | Low |
| T7: Weak RNG | Critical | Very Hard | Use CSPRNG | Very Low |
| T8: JPEG Corruption | Medium | Easy | PNG recommendation | Medium |
| T9: Timing Attack | Low | Very Hard | Constant-time crypto | Very Low |
| T10: Supply Chain | Critical | Very Hard | Vet dependencies | Low |

## Risk Assessment

### Critical Risks

- **Weak passphrases**: Users choose dictionary words
- **Keyloggers**: System compromised before use

**Mitigation**: User education and documentation

### High Risks

- **JPEG usage**: Users ignore PNG recommendation
- **Passphrase loss**: Users forget passphrase (irrecoverable)

**Mitigation**: Warnings and best practices docs

### Medium Risks

- **Memory dumps**: Mitigated by secure_wipe() on decrypted buffers (best-effort; residual risk low).
- **Social engineering**: Attacker tricks user into revealing passphrase

**Mitigation**: Security hardening, user awareness

### Low Risks

- **Steganalysis detection**: Doesn't reveal password
- **Side-channel attacks**: Libraries handle this

**Mitigation**: Already addressed by design

## Defense in Depth

### Layer 1: Cryptography

Primary defense. Even if stego is detected/removed, password remains encrypted.

### Layer 2: Key Derivation

Slows brute-force attacks. Strong passphrase requirement.

### Layer 3: Steganography

Obscurity layer. Makes backups look like regular photos.

### Layer 4: User Practices

Documentation, warnings, best practices guidance.

## Assumptions

### Security Assumptions

1. **Cryptographic libraries are secure**: PyNaCl, Argon2 have no backdoors
2. **OS CSPRNG is random**: `/dev/urandom` provides good entropy
3. **User's system is clean**: No malware when creating/restoring backups
4. **User chooses strong passphrase**: At least 12+ characters, non-dictionary

### Operational Assumptions

1. User reads and follows security documentation
2. User stores backups in multiple secure locations
3. User tests recovery periodically
4. User protects passphrase appropriately

## Future Threats

### Post-Quantum Cryptography

**Timeline**: 10-30 years

**Impact**: XChaCha20 vulnerable to quantum computers

**Mitigation Plan**: Migrate to post-quantum ciphers (future version)

### AI-Based Steganalysis

**Timeline**: 5-10 years

**Impact**: Better detection of LSB steganography

**Mitigation Plan**: Advanced embedding techniques (DCT, spread spectrum)

## Recommendations

### For Users

1. Use 16+ character random passphrases
2. Store passphrases securely (separate from backups)
3. Use PNG format exclusively
4. Keep multiple backup copies
5. Test recovery regularly
6. Never share backup images publicly

### For Developers

1. Keep dependencies updated
2. Monitor CVE databases
3. Use `stegvault.utils.secure_wipe()` for sensitive buffers (already integrated in vault/CLI/batch/gallery)
4. Consider post-quantum migration path
5. Regular security audits

## Next Steps

- Review [Security Model](Security-Model.md)
- Read [Known Limitations](Known-Limitations.md)
- Check [Security Best Practices](Security-Best-Practices.md)
- See [Vulnerability Disclosure](Vulnerability-Disclosure.md)
