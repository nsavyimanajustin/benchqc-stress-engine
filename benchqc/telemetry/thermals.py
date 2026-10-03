"""Thermal monitoring and hardware throttling detection module."""

import os
import sys
import glob
import platform
import subprocess
from typing import Optional, List, Tuple
from benchqc.schema import ThermalTelemetry
from benchqc.config import BenchConfig

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def _run_cmd(cmd: list[str]) -> str:
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2,
            check=False
        )
        return res.stdout.strip()
    except Exception:
        return ""


class ThermalMonitor:
    """Monitors CPU temperature and detects thermal throttling."""

    @staticmethod
    def get_current_temperature_c() -> Optional[float]:
        """Queries CPU/SoC temperatures across platforms."""
        if HAS_PSUTIL:
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Common keys: coretemp, k10temp, cpu_thermal, soc_thermal, acpitz
                    for name in ["coretemp", "k10temp", "cpu_thermal", "soc_thermal", "acpitz", "cpu-thermal"]:
                        if name in temps and temps[name]:
                            entries = temps[name]
                            vals = [e.current for e in entries if e.current is not None and e.current > 0]
                            if vals:
                                return round(sum(vals) / len(vals), 1)
                    # Any key
                    for name, entries in temps.items():
                        vals = [e.current for e in entries if e.current is not None and e.current > 0]
                        if vals:
                            return round(sum(vals) / len(vals), 1)
            except Exception:
                pass

        sys_name = platform.system()
        if sys_name == "Linux":
            # Direct sysfs thermal zones
            zones = glob.glob("/sys/class/thermal/thermal_zone*/temp")
            vals = []
            for z in zones:
                try:
                    with open(z, "r") as f:
                        val = int(f.read().strip())
                        # Usually millidegrees C
                        if val > 1000:
                            vals.append(val / 1000.0)
                        elif val > 0:
                            vals.append(float(val))
                except Exception:
                    continue
            if vals:
                return round(sum(vals) / len(vals), 1)

        elif sys_name == "Windows":
            # WMI ACPI Temperature (in tenths of Kelvin)
            wmi_out = _run_cmd([
                "powershell", "-NoProfile", "-Command",
                "(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue).CurrentTemperature"
            ])
            if wmi_out and wmi_out.isdigit():
                # Kelvin * 10 -> C = (K_10 / 10.0) - 273.15
                k10 = int(wmi_out)
                c = (k10 / 10.0) - 273.15
                if 20.0 <= c <= 115.0:
                    return round(c, 1)

        elif sys_name == "Darwin":
            out = _run_cmd(["osx-cpu-temp"])
            if "°C" in out:
                try:
                    return float(out.replace("°C", "").strip())
                except Exception:
                    pass

        return None

    @staticmethod
    def get_current_cpu_freq_ghz() -> float:
        """Returns average current CPU frequency in GHz."""
        if HAS_PSUTIL:
            try:
                freq = psutil.cpu_freq()
                if freq and freq.current > 0:
                    return round(freq.current / 1000.0, 3)
            except Exception:
                pass
                
        # Linux fallback
        if platform.system() == "Linux" and os.path.exists("/proc/cpuinfo"):
            try:
                with open("/proc/cpuinfo", "r") as f:
                    freqs = []
                    for line in f:
                        if "cpu MHz" in line:
                            mhz = float(line.split(":")[1].strip())
                            freqs.append(mhz)
                    if freqs:
                        return round((sum(freqs) / len(freqs)) / 1000.0, 3)
            except Exception:
                pass

        return 2.400  # Default nominal GHz baseline

    @classmethod
    def evaluate_throttling(
        cls,
        baseline_temp_c: float,
        peak_temp_c: float,
        baseline_freq_ghz: float,
        stress_freq_ghz: float,
        config: Optional[BenchConfig] = None
    ) -> ThermalTelemetry:
        """Evaluates thermal delta and throttling flags."""
        cfg = config or BenchConfig()
        delta_temp = round(peak_temp_c - baseline_temp_c, 1)
        
        freq_drop_pct = 0.0
        if baseline_freq_ghz > 0.1:
            freq_drop = max(0.0, baseline_freq_ghz - stress_freq_ghz)
            freq_drop_pct = round((freq_drop / baseline_freq_ghz) * 100.0, 1)

        throttle_detected = False
        throttling_pct = 0.0

        if freq_drop_pct >= cfg.thermal_throttle_freq_drop_pct and peak_temp_c >= 78.0:
            throttle_detected = True
            throttling_pct = freq_drop_pct
        elif peak_temp_c >= cfg.thermal_temp_critical_c:
            throttle_detected = True
            throttling_pct = round(max(freq_drop_pct, 12.5), 1)

        return ThermalTelemetry(
            baselineTempC=baseline_temp_c,
            peakTempC=peak_temp_c,
            deltaTempC=delta_temp,
            throttleDetected=throttle_detected,
            throttlingPercent=throttling_pct,
            frequencyBaselineGhz=baseline_freq_ghz,
            frequencyUnderStressGhz=stress_freq_ghz,
        )
