"""Storage I/O read/write stress testing module."""

import os
import time
import tempfile
import hashlib
import random
from typing import Dict, Any, Optional, Callable
from benchqc.config import BenchConfig


class StorageStressEngine:
    """Performs sequential and random read/write storage I/O benchmarks and integrity checks."""

    def __init__(
        self,
        duration_seconds: float = 6.0,
        file_size_mb: int = 64,
        target_dir: Optional[str] = None
    ):
        self.duration_seconds = max(1.0, float(duration_seconds))
        self.file_size_mb = max(8, file_size_mb)
        self.target_dir = target_dir

    def run(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        Executes sequential write, sequential read, random write, and random read tests.
        """
        temp_dir = self.target_dir or tempfile.gettempdir()
        test_file_path = os.path.join(temp_dir, f"benchqc_io_test_{os.getpid()}_{int(time.time())}.tmp")
        
        block_size = 64 * 1024  # 64 KB blocks for sequential
        num_blocks = (self.file_size_mb * 1024 * 1024) // block_size
        rand_4k_size = 4 * 1024  # 4 KB blocks for random IOPS
        
        errors = 0
        seq_write_mb_s = 0.0
        seq_read_mb_s = 0.0
        rand_write_iops = 0.0
        rand_read_iops = 0.0
        
        test_payload = os.urandom(block_size)
        file_hash = hashlib.sha256()

        try:
            # 1. Sequential Write Test
            if progress_callback:
                progress_callback(10.0, f"Storage: Sequential Write ({self.file_size_mb} MB)...")

            t0 = time.time()
            with open(test_file_path, "wb") as f:
                for i in range(num_blocks):
                    # Deterministic chunk based on block index
                    f.write(test_payload)
                    file_hash.update(test_payload)
                f.flush()
                os.fsync(f.fileno())
            t_seq_write = max(0.001, time.time() - t0)
            seq_write_mb_s = round(self.file_size_mb / t_seq_write, 1)

            expected_checksum = file_hash.hexdigest()

            # 2. Sequential Read & Integrity Verification Test
            if progress_callback:
                progress_callback(40.0, f"Storage: Sequential Read & Checksum Verification...")

            t0 = time.time()
            read_hash = hashlib.sha256()
            bytes_read = 0
            with open(test_file_path, "rb") as f:
                while True:
                    chunk = f.read(block_size)
                    if not chunk:
                        break
                    read_hash.update(chunk)
                    bytes_read += len(chunk)
            t_seq_read = max(0.001, time.time() - t0)
            seq_read_mb_s = round((bytes_read / (1024 * 1024)) / t_seq_read, 1)

            if read_hash.hexdigest() != expected_checksum:
                errors += 1

            # 3. Random 4KB Write IOPS Test
            if progress_callback:
                progress_callback(70.0, f"Storage: Random 4KB Write Stress...")

            rand_payload = os.urandom(rand_4k_size)
            max_seek_pos = max(0, (self.file_size_mb * 1024 * 1024) - rand_4k_size)
            
            t0 = time.time()
            writes_count = 0
            rand_write_time_limit = min(self.duration_seconds * 0.35, 2.0)
            
            with open(test_file_path, "r+b") as f:
                while (time.time() - t0) < rand_write_time_limit:
                    pos = random.randint(0, max_seek_pos // rand_4k_size) * rand_4k_size
                    f.seek(pos)
                    f.write(rand_payload)
                    writes_count += 1
                f.flush()
                os.fsync(f.fileno())
            
            t_rand_write = max(0.001, time.time() - t0)
            rand_write_iops = round(writes_count / t_rand_write, 1)

            # 4. Random 4KB Read IOPS Test
            if progress_callback:
                progress_callback(90.0, f"Storage: Random 4KB Read Stress...")

            t0 = time.time()
            reads_count = 0
            rand_read_time_limit = min(self.duration_seconds * 0.35, 2.0)
            
            with open(test_file_path, "rb") as f:
                while (time.time() - t0) < rand_read_time_limit:
                    pos = random.randint(0, max_seek_pos // rand_4k_size) * rand_4k_size
                    f.seek(pos)
                    data = f.read(rand_4k_size)
                    if len(data) != rand_4k_size:
                        errors += 1
                    reads_count += 1

            t_rand_read = max(0.001, time.time() - t0)
            rand_read_iops = round(reads_count / t_rand_read, 1)

        finally:
            # Safe cleanup
            if os.path.exists(test_file_path):
                try:
                    os.remove(test_file_path)
                except Exception:
                    pass

        passed = (errors == 0 and seq_write_mb_s > 5.0 and seq_read_mb_s > 5.0)

        if progress_callback:
            progress_callback(
                100.0,
                f"Storage Complete - Write: {seq_write_mb_s} MB/s, Read: {seq_read_mb_s} MB/s (Errors: {errors})"
            )

        return {
            "status": "PASSED" if passed else "FAILED",
            "fileSizeMb": self.file_size_mb,
            "seqWriteMbSec": seq_write_mb_s,
            "seqReadMbSec": seq_read_mb_s,
            "randWriteIops": rand_write_iops,
            "randReadIops": rand_read_iops,
            "errorsDetected": errors,
        }
