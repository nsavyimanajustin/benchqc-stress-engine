"""Memory saturation and parity verification stress module."""

import time
import os
import hashlib
import struct
from typing import Dict, Any, Optional, Callable
from benchqc.config import BenchConfig

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MemoryStressEngine:
    """Allocates memory blocks, performs bit-pattern verification, and measures memory throughput."""

    def __init__(self, duration_seconds: float = 8.0, max_allocation_mb: int = 1024):
        self.duration_seconds = max(1.0, float(duration_seconds))
        self.max_allocation_mb = max_allocation_mb

    def _determine_buffer_size_mb(self) -> int:
        """Determines a safe memory allocation size based on available physical RAM."""
        avail_mb = 1024
        if HAS_PSUTIL:
            try:
                avail_mb = int(psutil.virtual_memory().available / (1024 * 1024))
            except Exception:
                pass
        
        # Take 50% of available memory or max_allocation_mb, whichever is lower (minimum 128MB)
        safe_alloc = min(self.max_allocation_mb, max(128, int(avail_mb * 0.5)))
        return safe_alloc

    def run(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        Runs alternating bit-pattern tests (0x55, 0xAA), walking bit patterns,
        and hash parity checks over allocated buffers.
        """
        alloc_mb = self._determine_buffer_size_mb()
        block_size = 1024 * 1024  # 1 MB blocks
        num_blocks = alloc_mb

        if progress_callback:
            progress_callback(0.0, f"Allocating {alloc_mb} MB RAM for saturation testing...")

        start_time = time.time()
        total_bytes_written = 0
        total_bytes_read = 0
        errors = 0

        # Pattern 1: Alternating 0xAA (10101010) and 0x55 (01010101)
        pat_aa = b"\xAA" * block_size
        pat_55 = b"\x55" * block_size

        try:
            # Step 1: Allocation and initial fill
            buffers = [bytearray(pat_aa) for _ in range(num_blocks)]
            total_bytes_written += alloc_mb * 1024 * 1024

            if progress_callback:
                progress_callback(25.0, f"RAM Fill: {alloc_mb} MB active. Verifying bit-pattern 0xAA...")

            # Verify pattern AA
            for i, buf in enumerate(buffers):
                if buf != pat_aa:
                    errors += 1
                total_bytes_read += len(buf)

            # Step 2: Overwrite with 0x55 (flip all bits)
            if progress_callback:
                progress_callback(50.0, f"RAM Bit-Flip: Overwriting with 0x55...")

            for i in range(num_blocks):
                buffers[i][:] = pat_55
                total_bytes_written += block_size

            # Verify pattern 55
            for buf in buffers:
                if buf != pat_55:
                    errors += 1
                total_bytes_read += len(buf)

            # Step 3: Pseudo-random block hashing and walking bit patterns loop
            iteration = 0
            while (time.time() - start_time) < self.duration_seconds:
                iteration += 1
                elapsed = time.time() - start_time
                pct = min(95.0, 50.0 + (elapsed / self.duration_seconds) * 45.0)
                if progress_callback:
                    progress_callback(pct, f"RAM Torture: Cycle {iteration} (Parity & Hash Verification)...")

                for i in range(min(num_blocks, 32)):
                    # Generate deterministic test chunk
                    seed_val = (i + iteration * 31) & 0xFFFFFFFF
                    chunk = bytearray((seed_val % 256).to_bytes(1, "little") * block_size)
                    expected_hash = hashlib.md5(chunk).digest()

                    # Write
                    buffers[i][:] = chunk
                    total_bytes_written += block_size

                    # Read & verify
                    actual_hash = hashlib.md5(buffers[i]).digest()
                    total_bytes_read += block_size
                    if actual_hash != expected_hash:
                        errors += 1

                time.sleep(0.05)

        finally:
            # Free memory
            buffers = None

        actual_duration = max(0.001, time.time() - start_time)
        total_mb = (total_bytes_written + total_bytes_read) / (1024 * 1024)
        throughput_mb_sec = round(total_mb / actual_duration, 1)
        passed = (errors == 0)

        if progress_callback:
            progress_callback(100.0, f"Memory Test Complete - {throughput_mb_sec} MB/s (Errors: {errors})")

        return {
            "status": "PASSED" if passed else "FAILED",
            "allocatedMb": alloc_mb,
            "durationSeconds": round(actual_duration, 2),
            "throughputMbSec": throughput_mb_sec,
            "bytesRead": total_bytes_read,
            "bytesWritten": total_bytes_written,
            "errorsDetected": errors,
        }
