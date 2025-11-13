#!/usr/bin/env python3
"""
Performance benchmarking script for StegVault.

Tests backup and restore operations across different image sizes
and measures execution time, memory usage, and throughput.
"""

import time
import os
import sys
import traceback
from pathlib import Path
from typing import List, Tuple
import tracemalloc
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from stegvault.crypto import encrypt_data, decrypt_data
from stegvault.stego import embed_payload, extract_payload, calculate_capacity
from stegvault.utils import serialize_payload, parse_payload


class BenchmarkResult:
    """Store benchmark results."""

    def __init__(self, name: str, image_size: Tuple[int, int], password_length: int):
        self.name = name
        self.image_size = image_size
        self.password_length = password_length
        self.encryption_time = 0.0
        self.embedding_time = 0.0
        self.extraction_time = 0.0
        self.decryption_time = 0.0
        self.total_backup_time = 0.0
        self.total_restore_time = 0.0
        self.peak_memory_mb = 0.0
        self.capacity_bytes = 0
        self.payload_size_bytes = 0

    def __str__(self) -> str:
        """Format results as string."""
        return (
            f"\n{'='*70}\n"
            f"Benchmark: {self.name}\n"
            f"{'='*70}\n"
            f"Image Size:        {self.image_size[0]}x{self.image_size[1]} "
            f"({self.image_size[0] * self.image_size[1]:,} pixels)\n"
            f"Password Length:   {self.password_length} characters\n"
            f"Image Capacity:    {self.capacity_bytes:,} bytes\n"
            f"Payload Size:      {self.payload_size_bytes} bytes\n"
            f"Capacity Usage:    {(self.payload_size_bytes/self.capacity_bytes)*100:.2f}%\n"
            f"\n"
            f"Backup Performance:\n"
            f"  Encryption:      {self.encryption_time*1000:.2f} ms\n"
            f"  Embedding:       {self.embedding_time*1000:.2f} ms\n"
            f"  Total:           {self.total_backup_time*1000:.2f} ms\n"
            f"\n"
            f"Restore Performance:\n"
            f"  Extraction:      {self.extraction_time*1000:.2f} ms\n"
            f"  Decryption:      {self.decryption_time*1000:.2f} ms\n"
            f"  Total:           {self.total_restore_time*1000:.2f} ms\n"
            f"\n"
            f"Memory Usage:\n"
            f"  Peak:            {self.peak_memory_mb:.2f} MB\n"
        )


def create_test_image(width: int, height: int, output_path: str) -> None:
    """Create a gradient test image."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = int(255 * (x + y) / (width + height))
            pixels[x, y] = (r, g, b)

    img.save(output_path, "PNG")


def benchmark_operation(
    name: str, image_path: str, password: str, passphrase: str
) -> BenchmarkResult:
    """Benchmark a complete backup and restore operation."""
    import tempfile

    # Load image for capacity check
    with Image.open(image_path) as img:
        width, height = img.size
        result = BenchmarkResult(name, (width, height), len(password))
        result.capacity_bytes = calculate_capacity(img)

    password_bytes = password.encode("utf-8")

    # Start memory tracking
    tracemalloc.start()

    # ===== BACKUP OPERATION =====
    backup_start = time.perf_counter()

    # Encryption phase
    encrypt_start = time.perf_counter()
    ciphertext, salt, nonce = encrypt_data(password_bytes, passphrase)
    encrypt_end = time.perf_counter()
    result.encryption_time = encrypt_end - encrypt_start

    # Serialize payload
    payload = serialize_payload(salt, nonce, ciphertext)
    result.payload_size_bytes = len(payload)

    # Derive seed from salt
    seed = int.from_bytes(salt[:4], byteorder="big")

    # Embedding phase
    embed_start = time.perf_counter()
    # Create temp file for stego image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        temp_stego_path = tmp.name

    stego_img = embed_payload(image_path, payload, seed, temp_stego_path)
    stego_img.close()
    embed_end = time.perf_counter()
    result.embedding_time = embed_end - embed_start

    backup_end = time.perf_counter()
    result.total_backup_time = backup_end - backup_start

    # ===== RESTORE OPERATION =====
    restore_start = time.perf_counter()

    # Extraction phase
    extract_start = time.perf_counter()
    extracted_payload = extract_payload(temp_stego_path, len(payload), seed)
    extract_end = time.perf_counter()
    result.extraction_time = extract_end - extract_start

    # Decryption phase
    decrypt_start = time.perf_counter()
    salt2, nonce2, ciphertext2 = parse_payload(extracted_payload)
    recovered_password_bytes = decrypt_data(ciphertext2, salt2, nonce2, passphrase)
    decrypt_end = time.perf_counter()
    result.decryption_time = decrypt_end - decrypt_start

    restore_end = time.perf_counter()
    result.total_restore_time = restore_end - restore_start

    # Memory usage
    current, peak = tracemalloc.get_traced_memory()
    result.peak_memory_mb = peak / 1024 / 1024
    tracemalloc.stop()

    # Cleanup temp file
    os.unlink(temp_stego_path)

    # Verify correctness
    assert recovered_password_bytes.decode("utf-8") == password, "Password mismatch!"

    return result


def run_benchmarks() -> List[BenchmarkResult]:
    """Run all benchmarks."""

    results = []
    test_password = "SecurePassword123!@#"
    test_passphrase = "BenchmarkPassphrase2024"

    # Test configurations: (name, width, height)
    test_configs = [
        ("Small (100x100)", 100, 100),
        ("Medium (500x500)", 500, 500),
        ("Large (1000x1000)", 1000, 1000),
        ("HD Ready (1280x720)", 1280, 720),
        ("Full HD (1920x1080)", 1920, 1080),
        ("4K (3840x2160)", 3840, 2160),
    ]

    print("StegVault Performance Benchmark")
    print("=" * 70)
    print(f"Password Length: {len(test_password)} characters")
    print(f"Passphrase Length: {len(test_passphrase)} characters")
    print(f"Python Version: {sys.version.split()[0]}")
    print()

    for name, width, height in test_configs:
        print(f"Running benchmark: {name}...", end=" ", flush=True)

        # Create test image
        image_path = f"benchmark_{width}x{height}.png"
        create_test_image(width, height, image_path)

        try:
            # Run benchmark
            result = benchmark_operation(name, image_path, test_password, test_passphrase)
            results.append(result)
            print("[OK]")
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            traceback.print_exc()
        finally:
            # Cleanup
            if os.path.exists(image_path):
                os.remove(image_path)

    return results


def print_summary(results: List[BenchmarkResult]) -> None:
    """Print summary table of all results."""

    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print()

    # Individual results
    for result in results:
        print(result)

    # Comparative table
    print("\n" + "=" * 70)
    print("COMPARATIVE TABLE")
    print("=" * 70)
    print()
    print(
        f"{'Image Size':<20} {'Pixels':<12} {'Backup (ms)':<15} {'Restore (ms)':<15} {'Memory (MB)':<12}"
    )
    print("-" * 70)

    for result in results:
        size_str = f"{result.image_size[0]}x{result.image_size[1]}"
        pixels = result.image_size[0] * result.image_size[1]
        print(
            f"{size_str:<20} {pixels:<12,} {result.total_backup_time*1000:<15.2f} "
            f"{result.total_restore_time*1000:<15.2f} {result.peak_memory_mb:<12.2f}"
        )

    # Performance metrics
    if results:
        print("\n" + "=" * 70)
        print("PERFORMANCE METRICS")
        print("=" * 70)
        print()

        # Average times
        avg_backup = sum(r.total_backup_time for r in results) / len(results)
        avg_restore = sum(r.total_restore_time for r in results) / len(results)
        avg_memory = sum(r.peak_memory_mb for r in results) / len(results)

        print(f"Average Backup Time:  {avg_backup*1000:.2f} ms")
        print(f"Average Restore Time: {avg_restore*1000:.2f} ms")
        print(f"Average Memory Usage: {avg_memory:.2f} MB")
        print()

        # Throughput (operations per second)
        print(f"Backup Throughput:    {1/avg_backup:.2f} ops/sec")
        print(f"Restore Throughput:   {1/avg_restore:.2f} ops/sec")
        print()

        # Pixel processing rate
        total_pixels = sum(r.image_size[0] * r.image_size[1] for r in results)
        total_time = sum(r.total_backup_time + r.total_restore_time for r in results)
        pixels_per_sec = total_pixels / total_time

        print(f"Pixel Processing Rate: {pixels_per_sec:,.0f} pixels/sec")


def main() -> None:
    """Main entry point."""

    try:
        results = run_benchmarks()
        print_summary(results)

        print("\n" + "=" * 70)
        print("Benchmark completed successfully!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nBenchmark failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
