"""Automated tests for BenchQC hardware stress engine, battery profiler, and audit emission."""

import os
import json
import pytest
from benchqc.config import (
    BenchConfig,
    calculate_grade,
    BADGE_STUDENT_APPROVED,
    BADGE_CAMPUS_READY,
    BADGE_NEEDS_CHARGER,
)
from benchqc.schema import (
    BenchQCAudit,
    SystemSpecs,
    BatteryTelemetry,
    ThermalTelemetry,
    QCSummary,
)
from benchqc.telemetry.system_info import collect_system_specs
from benchqc.telemetry.battery import BatteryReader
from benchqc.telemetry.thermals import ThermalMonitor
from benchqc.stress.cpu_torture import CPUTortureEngine
from benchqc.stress.memory_stress import MemoryStressEngine
from benchqc.stress.storage_stress import StorageStressEngine
from benchqc.sustenance.battery_profiler import BatteryProfiler
from benchqc.engine import BenchQCEngine


def test_system_specs_collector():
    """Verify system info collector correctly populates OS, CPU, RAM, and Storage."""
    specs = collect_system_specs()
    assert specs.os != ""
    assert specs.cpu != ""
    assert specs.cpuCores >= 1
    assert specs.cpuThreads >= specs.cpuCores or specs.cpuThreads >= 1
    assert specs.ramGb > 0.0
    assert specs.storageGb > 0.0
    assert specs.architecture != ""


def test_battery_reader_and_badges():
    """Verify battery telemetry and student sustenance badge thresholds."""
    bat = BatteryReader.get_telemetry()
    assert bat.designCapacityMwh > 0
    assert bat.fullCapacityMwh > 0
    assert 0.0 <= bat.healthPercent <= 100.0
    assert 0.0 <= bat.wearPercent <= 100.0
    assert bat.projectedHoursStudent > 0
    assert bat.studentBadge in [
        BADGE_STUDENT_APPROVED,
        BADGE_CAMPUS_READY,
        BADGE_NEEDS_CHARGER,
    ]


def test_student_sustenance_badge_rules():
    """Verify student badge calculation criteria."""
    # Test >= 4.0h
    p = BatteryProfiler(sample_duration_seconds=3.0)
    b_telemetry, suit = p.run_multi_tier_profiling()
    assert suit.badge in [
        BADGE_STUDENT_APPROVED,
        BADGE_CAMPUS_READY,
        BADGE_NEEDS_CHARGER,
    ]
    assert suit.expectedClassroomBatteryLife != ""
    assert "webBrowsingAndResearch" in suit.workloadReadiness


def test_thermal_monitor_throttling():
    """Verify thermal monitoring and throttling detection logic."""
    temp = ThermalMonitor.get_current_temperature_c()
    # If sensor available, must be reasonable CPU temp (15C to 115C)
    if temp is not None:
        assert 15.0 <= temp <= 115.0

    # Test normal thermals (no throttling)
    normal = ThermalMonitor.evaluate_throttling(
        baseline_temp_c=40.0,
        peak_temp_c=65.0,
        baseline_freq_ghz=3.2,
        stress_freq_ghz=3.1,
    )
    assert not normal.throttleDetected
    assert normal.throttlingPercent == 0.0

    # Test severe throttling
    throttled = ThermalMonitor.evaluate_throttling(
        baseline_temp_c=50.0,
        peak_temp_c=98.0,
        baseline_freq_ghz=3.5,
        stress_freq_ghz=2.2,  # >35% drop
    )
    assert throttled.throttleDetected
    assert throttled.throttlingPercent > 18.0


def test_cpu_torture_module():
    """Verify multi-core CPU torture execution and FLOPs measurement."""
    engine = CPUTortureEngine(duration_seconds=1.5, core_count=2)
    results = engine.run()
    assert results["status"] == "PASSED"
    assert results["errorsDetected"] == 0
    assert results["floatingPointOpsSec"] > 0
    assert results["cpuScore"] > 0


def test_memory_stress_module():
    """Verify RAM saturation, alternating bit patterns, and hash parity."""
    engine = MemoryStressEngine(duration_seconds=1.5, max_allocation_mb=64)
    results = engine.run()
    assert results["status"] == "PASSED"
    assert results["errorsDetected"] == 0
    assert results["throughputMbSec"] > 0


def test_storage_stress_module(tmp_path):
    """Verify sequential and random storage I/O and integrity."""
    engine = StorageStressEngine(duration_seconds=1.5, file_size_mb=16, target_dir=str(tmp_path))
    results = engine.run()
    assert results["status"] == "PASSED"
    assert results["errorsDetected"] == 0
    assert results["seqWriteMbSec"] > 0
    assert results["seqReadMbSec"] > 0


def test_grade_calculation():
    """Verify certified grade threshold assignments."""
    assert calculate_grade(98.5) == "A+"
    assert calculate_grade(93.0) == "A+"
    assert calculate_grade(88.0) == "A"
    assert calculate_grade(75.0) == "B"
    assert calculate_grade(60.0) == "C"
    assert calculate_grade(42.0) == "F"


def test_full_engine_quick_run_and_json_export(tmp_path):
    """End-to-end test of quick audit execution and JSON artifact validity."""
    output_json = str(tmp_path / "benchqc_audit.json")
    cfg = BenchConfig.quick()
    engine = BenchQCEngine(config=cfg)

    audit = engine.run_full_suite(output_file=output_json)

    assert os.path.exists(output_json)
    assert audit.auditId.startswith("BQC-")
    assert audit.certifiedGrade in ["A+", "A", "B", "C", "F"]
    assert 0.0 <= audit.overallScore <= 100.0
    assert audit.system.cpuCores >= 1
    assert audit.battery.projectedHoursStudent > 0
    assert audit.qcSummary.passedChecksCount >= 1

    # Verify JSON file on disk matches schema
    with open(output_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "auditId" in data
    assert "auditDate" in data
    assert "certifiedGrade" in data
    assert "overallScore" in data
    assert "system" in data
    assert "battery" in data
    assert "thermals" in data
    assert "qcSummary" in data
    assert "studentSuitability" in data
    assert "benchmarks" in data
    assert "officialVerificationUrl" in data

    # Verify reload from JSON
    reloaded = BenchQCAudit.from_file(output_json)
    assert reloaded.auditId == audit.auditId
    assert reloaded.certifiedGrade == audit.certifiedGrade
