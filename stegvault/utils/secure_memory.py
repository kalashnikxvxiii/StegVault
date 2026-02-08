"""
Secure memory handling for sensitive data.

Provides best-effort clearing of mutable buffers to reduce exposure
of secrets in RAM (mitigates T6: Memory Dump Attack in threat model).

Note: Python str and bytes are immutable and cannot be overwritten.
Use bytearray for sensitive data when possible, then call secure_wipe
when done. Callers of decrypt_data receive bytearray and must wipe
after use.
"""

from typing import Union


def secure_wipe(buf: Union[bytearray, memoryview]) -> None:
    """
    Overwrite a mutable buffer with zeros in place.

    Reduces the time window where plaintext secrets remain in RAM
    after use. No-op if buf is None or length zero.

    Args:
        buf: Mutable buffer (bytearray or writable memoryview) to wipe.
             Immutable types (bytes, str) are not supported and will
             be ignored (no exception) to allow safe use in finally blocks.

    Note:
        - Python cannot guarantee that copies of the data do not exist
          elsewhere (e.g. in the interpreter or C extensions).
        - This is a best-effort mitigation, not a guarantee.
    """
    if buf is None:
        return
    if isinstance(buf, (bytes, str)):
        # Immutable: cannot wipe; caller should not pass these
        return
    n = len(buf)
    if n == 0:
        return
    try:
        if isinstance(buf, bytearray):
            for i in range(n):
                buf[i] = 0
        elif isinstance(buf, memoryview):
            # Writable memoryview: assign zeros. Skip if read-only or no writable attr (e.g. Py3.14).
            try:
                buf[:] = b"\x00" * n
            except (TypeError, ValueError, AttributeError):
                pass
        # else: unsupported type, skip
    except (TypeError, ValueError):
        pass
