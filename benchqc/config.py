"""Configuration and calibration constants for BenchQC Stress Engine."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class BenchConfig:
    # Execution mode
    quick_mode: bool = False
    duration_factor: float = 1.0
    
    # Stress durations (in seconds)
    cpu_stress_seconds: int = 15
    memory_stress_seconds: int = 10
    storage_stress_seconds: int = 10
    battery_sampling_seconds: int = 12
    
    # Quick mode override durations
    quick_cpu_seconds: int = 3
    quick_memory_seconds: int = 2
    quick_storage_seconds: int = 2
    quick_battery_seconds: int = 3

    # Battery thresholds for student badges (in hours)
    badge_4h_threshold: float = 4.0
    badge_3h_threshold: float = 3.0
    
    # Memory test config
    memory_max_mb: int = 2048
    memory_quick_mb: int = 512
    memory_target_percent: float = 65.0  # target 65% of available RAM
    
    # Storage test config
    storage_test_file_size_mb: int = 128
    storage_quick_file_size_mb: int = 32
    storage_block_size_kb: int = 64
    
    # Thermal Throttling detection
    thermal_throttle_freq_drop_pct: float = 18.0  # >=18% sustained frequency drop indicates thermal throttling
    thermal_temp_critical_c: float = 94.0

    @classmethod
    def standard(cls) -> "BenchConfig":
        return cls(quick_mode=False)

    @classmethod
    def quick(cls) -> "BenchConfig":
        return cls(
            quick_mode=True,
            cpu_stress_seconds=3,
            memory_stress_seconds=2,
            storage_stress_seconds=2,
            battery_sampling_seconds=3,
            storage_test_file_size_mb=32,
            memory_max_mb=512,
        )


# Badge Constants
BADGE_STUDENT_APPROVED = "STUDENT_APPROVED_4H_PLUS"
BADGE_CAMPUS_READY = "CAMPUS_READY_3H_TO_4H"
BADGE_NEEDS_CHARGER = "NEEDS_CHARGER_LESS_THAN_3H"

# Grade thresholds
GRADE_THRESHOLDS = [
    (93.0, "A+"),
    (84.0, "A"),
    (70.0, "B"),
    (55.0, "C"),
    (0.0, "F"),
]


def calculate_grade(overall_score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if overall_score >= threshold:
            return grade
    return "F"
