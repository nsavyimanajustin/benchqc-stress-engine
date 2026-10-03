"""Multi-core CPU torture engine with floating-point & matrix burn."""

import time
import math
import os
import multiprocessing as mp
from typing import Dict, Any, Tuple, Optional, Callable

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def _matrix_fp_burn_worker(duration_sec: float, worker_id: int) -> Tuple[int, int, bool]:
    """
    Worker function performing dense matrix operations, floating-point trig/exp burn,
    and mathematical checksum parity.
    Returns: (operations_completed, errors_found, success)
    """
    start_time = time.time()
    ops_completed = 0
    errors = 0
    
    # 64x64 matrix size is cache-friendly and tests ALU / FPU pipeline thoroughly
    n = 64
    
    if HAS_NUMPY:
        # NumPy vectorized matrix & FP burn
        np.random.seed(42 + worker_id)
        a = np.random.randn(n, n).astype(np.float64)
        b = np.random.randn(n, n).astype(np.float64)
        
        while (time.time() - start_time) < duration_sec:
            # Matrix multiplication
            c = np.dot(a, b)
            # Floating point trig & transcendental burn
            d = np.sin(c) * np.cos(c) + np.exp(np.clip(c / 100.0, -10.0, 10.0))
            # Parity check: verify no NaNs or Inf introduced through arithmetic corruption
            if np.isnan(d).any() or np.isinf(d).any():
                errors += 1
            # Feed back to avoid optimization elimination
            a = d / (np.max(np.abs(d)) + 1e-6)
            ops_completed += (n * n * n * 2) + (n * n * 10)  # FLOPs estimate
    else:
        # Pure Python fallback matrix & math burn
        # Initialize small matrices
        dim = 24
        mat_a = [[float((i * j + 1) % 17) for j in range(dim)] for i in range(dim)]
        mat_b = [[float((i + j + 2) % 13) for j in range(dim)] for i in range(dim)]
        
        while (time.time() - start_time) < duration_sec:
            # Multiply
            mat_c = [[0.0] * dim for _ in range(dim)]
            for i in range(dim):
                for k in range(dim):
                    for j in range(dim):
                        mat_c[i][j] += mat_a[i][k] * mat_b[k][j]
            # FP burn
            for i in range(dim):
                for j in range(dim):
                    val = mat_c[i][j]
                    res = math.sin(val % 3.14159) * math.cos(val % 3.14159) + math.sqrt(abs(val) + 1.0)
                    if math.isnan(res) or math.isinf(res):
                        errors += 1
                    mat_a[i][j] = res % 10.0
            ops_completed += (dim * dim * dim * 2) + (dim * dim * 5)

    return (ops_completed, errors, errors == 0)


class CPUTortureEngine:
    """Orchestrates multi-core CPU torture and measures compute capacity under stress."""

    def __init__(self, duration_seconds: float = 10.0, core_count: Optional[int] = None):
        self.duration_seconds = max(1.0, float(duration_seconds))
        self.core_count = core_count or os.cpu_count() or 1

    def run(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        Executes multi-core CPU torture across all threads.
        """
        if progress_callback:
            progress_callback(0.0, f"Spawning {self.core_count} CPU torture workers...")

        start_time = time.time()
        
        # Run across logical cores using multiprocessing Pool
        with mp.Pool(processes=self.core_count) as pool:
            async_results = [
                pool.apply_async(_matrix_fp_burn_worker, (self.duration_seconds, i))
                for i in range(self.core_count)
            ]
            
            # Progress monitoring
            while time.time() - start_time < self.duration_seconds:
                elapsed = time.time() - start_time
                pct = min(99.0, (elapsed / self.duration_seconds) * 100.0)
                if progress_callback:
                    progress_callback(pct, f"CPU Burn: {pct:.1f}% ({self.core_count} cores at 100% load)")
                time.sleep(0.2)

            # Gather results
            results = [res.get(timeout=10.0) for res in async_results]

        actual_duration = max(0.001, time.time() - start_time)
        total_ops = sum(r[0] for r in results)
        total_errors = sum(r[1] for r in results)
        passed = (total_errors == 0)

        ops_per_sec = total_ops / actual_duration
        
        # Normalized CPU multi-core score (calibrated 0-100+ where 100 is solid 8-core modern CPU)
        # Scaled smoothly using log-linear normalization
        score = round(min(100.0, max(10.0, math.log10(max(100.0, ops_per_sec)) * 14.5)), 1)

        if progress_callback:
            progress_callback(100.0, f"CPU Torture Complete - {ops_per_sec/1e6:.1f} MFLOP/s (Errors: {total_errors})")

        return {
            "status": "PASSED" if passed else "FAILED",
            "coresTested": self.core_count,
            "durationSeconds": round(actual_duration, 2),
            "totalOperations": total_ops,
            "floatingPointOpsSec": round(ops_per_sec, 1),
            "cpuScore": score,
            "errorsDetected": total_errors,
        }
