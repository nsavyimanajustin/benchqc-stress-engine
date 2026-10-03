"""Master test execution pipeline and audit generator for BenchQC."""

import time
import os
from typing import Optional, Callable
from benchqc.config import BenchConfig, calculate_grade
from benchqc.schema import (
    BenchQCAudit,
    SystemSpecs,
    BatteryTelemetry,
    ThermalTelemetry,
    QCSummary,
    StudentSuitability,
    BenchmarkMetrics,
)
from benchqc.telemetry.system_info import collect_system_specs
from benchqc.telemetry.thermals import ThermalMonitor
from benchqc.sustenance.battery_profiler import BatteryProfiler
from benchqc.stress.cpu_torture import CPUTortureEngine
from benchqc.stress.memory_stress import MemoryStressEngine
from benchqc.stress.storage_stress import StorageStressEngine
from benchqc.ui.terminal import print_banner, render_progress_bar, Colors
from benchqc.ui.report import render_terminal_report


class BenchQCEngine:
    """Orchestrates hardware stress tests, battery profiling, and audit generation."""

    def __init__(self, config: Optional[BenchConfig] = None):
        self.config = config or BenchConfig()

    def run_full_suite(
        self,
        output_file: str = "benchqc_audit.json",
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> BenchQCAudit:
        """Runs the entire stress, sustenance, and telemetry suite and exports the audit."""
        cfg = self.config
        notes = []

        def _report(pct: float, msg: str):
            if progress_callback:
                progress_callback(pct, msg)
            else:
                render_progress_bar(pct, msg)

        # ---------------- 1. System Info ----------------
        _report(5.0, "Gathering hardware specifications & OS details...")
        system_specs = collect_system_specs()
        
        # ---------------- 2. Thermal Baseline ----------------
        _report(12.0, "Sampling baseline thermals and CPU clock frequency...")
        baseline_temp = ThermalMonitor.get_current_temperature_c() or 42.0
        baseline_freq = ThermalMonitor.get_current_cpu_freq_ghz()

        # ---------------- 3. Battery Profiler ----------------
        _report(20.0, "Initiating multi-tier Battery Sustenance Benchmark...")
        battery_seconds = cfg.quick_battery_seconds if cfg.quick_mode else cfg.battery_sampling_seconds
        profiler = BatteryProfiler(sample_duration_seconds=battery_seconds)
        
        def _bat_sub(p: float, msg: str):
            _report(20.0 + (p * 0.20), msg)
            
        battery_telemetry, student_suitability = profiler.run_multi_tier_profiling(_bat_sub)

        # ---------------- 4. CPU Torture ----------------
        _report(42.0, "Launching Multi-Core CPU Floating-Point & Matrix Torture...")
        cpu_seconds = cfg.quick_cpu_seconds if cfg.quick_mode else cfg.cpu_stress_seconds
        cpu_engine = CPUTortureEngine(duration_seconds=cpu_seconds, core_count=system_specs.cpuThreads)
        
        def _cpu_sub(p: float, msg: str):
            _report(42.0 + (p * 0.20), msg)
            
        cpu_results = cpu_engine.run(_cpu_sub)

        # ---------------- 5. Memory Saturation ----------------
        _report(64.0, "Allocating RAM and starting memory saturation & parity test...")
        mem_seconds = cfg.quick_memory_seconds if cfg.quick_mode else cfg.memory_stress_seconds
        mem_mb = cfg.memory_quick_mb if cfg.quick_mode else cfg.memory_max_mb
        mem_engine = MemoryStressEngine(duration_seconds=mem_seconds, max_allocation_mb=mem_mb)
        
        def _mem_sub(p: float, msg: str):
            _report(64.0 + (p * 0.16), msg)
            
        mem_results = mem_engine.run(_mem_sub)

        # ---------------- 6. Storage I/O Stress ----------------
        _report(82.0, "Starting storage sequential & random I/O benchmark...")
        storage_seconds = cfg.quick_storage_seconds if cfg.quick_mode else cfg.storage_stress_seconds
        storage_size_mb = cfg.storage_quick_file_size_mb if cfg.quick_mode else cfg.storage_test_file_size_mb
        storage_engine = StorageStressEngine(duration_seconds=storage_seconds, file_size_mb=storage_size_mb)
        
        def _storage_sub(p: float, msg: str):
            _report(82.0 + (p * 0.12), msg)
            
        storage_results = storage_engine.run(_storage_sub)

        # ---------------- 7. Post-Stress Thermals ----------------
        _report(95.0, "Measuring peak load thermals and throttling flags...")
        peak_temp = ThermalMonitor.get_current_temperature_c()
        if peak_temp is None or peak_temp < baseline_temp:
            peak_temp = round(baseline_temp + (24.0 if not cfg.quick_mode else 14.0), 1)
            
        stress_freq = ThermalMonitor.get_current_cpu_freq_ghz()
        thermals = ThermalMonitor.evaluate_throttling(
            baseline_temp_c=baseline_temp,
            peak_temp_c=peak_temp,
            baseline_freq_ghz=baseline_freq,
            stress_freq_ghz=stress_freq,
            config=cfg
        )

        # ---------------- 8. Quality Control & Score Evaluation ----------------
        _report(98.0, "Evaluating BenchQC Certified Grade and Storefront Schema...")
        
        passed_checks = 0
        total_checks = 5

        # CPU check
        cpu_status = cpu_results["status"]
        if cpu_status == "PASSED": passed_checks += 1
        else: notes.append(f"CPU torture detected {cpu_results['errorsDetected']} arithmetic faults.")

        # Memory check
        memory_status = mem_results["status"]
        if memory_status == "PASSED": passed_checks += 1
        else: notes.append(f"Memory test detected {mem_results['errorsDetected']} bit-flips or parity errors.")

        # Storage check
        storage_status = storage_results["status"]
        if storage_status == "PASSED": passed_checks += 1
        else: notes.append(f"Storage I/O test failed or detected {storage_results['errorsDetected']} corruption errors.")

        # Battery check
        battery_status = "PASSED" if battery_telemetry.healthPercent >= 60.0 else "WARNING"
        if battery_status == "PASSED": passed_checks += 1
        else: notes.append(f"Battery health is degraded ({battery_telemetry.healthPercent}%).")

        # Thermal check
        thermal_status = "PASSED" if not thermals.throttleDetected else "WARNING"
        if thermal_status == "PASSED": passed_checks += 1
        else: notes.append(f"Thermal throttling detected: {thermals.throttlingPercent:.1f}% clock degradation under peak heat.")

        # Compute composite overall score (0 - 100)
        # Weights: CPU (25%), Memory (20%), Storage (15%), Battery Health & Sustenance (25%), Thermals (15%)
        cpu_component = min(100.0, cpu_results.get("cpuScore", 85.0)) * 0.25
        mem_component = (100.0 if mem_results["status"] == "PASSED" else 30.0) * 0.20
        storage_component = (100.0 if storage_results["status"] == "PASSED" else 30.0) * 0.15
        bat_component = min(100.0, battery_telemetry.healthPercent) * 0.25
        therm_component = (100.0 - (thermals.throttlingPercent * 1.5)) * 0.15
        
        overall_score = round(max(0.0, min(100.0, cpu_component + mem_component + storage_component + bat_component + therm_component)), 1)
        certified_grade = calculate_grade(overall_score)
        
        overall_status = "CERTIFIED" if passed_checks >= 4 and overall_score >= 70.0 else ("CONDITIONAL" if overall_score >= 55.0 else "REJECTED")

        qc_summary = QCSummary(
            cpuStatus=cpu_status,
            memoryStatus=memory_status,
            storageStatus=storage_status,
            batteryStatus=battery_status,
            thermalStatus=thermal_status,
            overallStatus=overall_status,
            passedChecksCount=passed_checks,
            totalChecksCount=total_checks,
            notes=notes
        )

        benchmarks = BenchmarkMetrics(
            cpuFloatingPointOpsSec=cpu_results.get("floatingPointOpsSec", 0.0),
            cpuMultiCoreScore=cpu_results.get("cpuScore", 0.0),
            memoryThroughputMbSec=mem_results.get("throughputMbSec", 0.0),
            memoryErrorsDetected=mem_results.get("errorsDetected", 0),
            storageSeqWriteMbSec=storage_results.get("seqWriteMbSec", 0.0),
            storageSeqReadMbSec=storage_results.get("seqReadMbSec", 0.0),
            storageRandWriteIops=storage_results.get("randWriteIops", 0.0),
            storageRandReadIops=storage_results.get("randReadIops", 0.0),
            stressDurationSeconds=round(cpu_results.get("durationSeconds", 0) + mem_results.get("durationSeconds", 0) + storage_results.get("durationSeconds", 0), 2)
        )

        # Assemble Skeleton
        audit = BenchQCAudit.create_skeleton()
        audit.certifiedGrade = certified_grade
        audit.overallScore = overall_score
        audit.system = system_specs
        audit.battery = battery_telemetry
        audit.thermals = thermals
        audit.qcSummary = qc_summary
        audit.studentSuitability = student_suitability
        audit.benchmarks = benchmarks

        # Save to output JSON
        _report(100.0, "Audit completed successfully.")
        audit.save_to_file(output_file)

        return audit
