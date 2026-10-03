"""Cross-platform system hardware and OS information collector."""

import os
import platform
import subprocess
import shutil
import sys
from typing import Optional
from benchqc.schema import SystemSpecs

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
            timeout=3,
            check=False
        )
        return res.stdout.strip()
    except Exception:
        return ""


def get_os_details() -> tuple[str, str]:
    """Returns (os_name, os_version)."""
    system = platform.system()
    if system == "Windows":
        version = platform.version()
        release = platform.release()
        return f"Windows {release}", version
    elif system == "Darwin":
        mac_ver = platform.mac_ver()[0]
        return f"macOS {mac_ver}", platform.version()
    else:
        # Linux
        distro_name = ""
        if os.path.exists("/etc/os-release"):
            try:
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            distro_name = line.split("=", 1)[1].strip().strip('"')
                            break
            except Exception:
                pass
        if not distro_name:
            distro_name = f"Linux ({platform.release()})"
        return distro_name, platform.release()


def get_cpu_info() -> tuple[str, int, int]:
    """Returns (cpu_model, physical_cores, logical_threads)."""
    logical_cores = os.cpu_count() or 1
    physical_cores = logical_cores
    
    if HAS_PSUTIL:
        phys = psutil.cpu_count(logical=False)
        if phys:
            physical_cores = phys

    cpu_name = ""
    system = platform.system()
    
    if system == "Windows":
        # Try registry or wmic / powershell
        cpu_name = _run_cmd(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"])
        if not cpu_name:
            cpu_name = platform.processor()
    elif system == "Darwin":
        cpu_name = _run_cmd(["sysctl", "-n", "machdep.cpu.brand_string"])
        if not cpu_name:
            cpu_name = platform.processor()
    else:
        # Linux
        if os.path.exists("/proc/cpuinfo"):
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            cpu_name = line.split(":", 1)[1].strip()
                            break
            except Exception:
                pass
        if not cpu_name:
            cpu_name = _run_cmd(["lscpu"])
            for line in cpu_name.splitlines():
                if "Model name:" in line:
                    cpu_name = line.split(":", 1)[1].strip()
                    break

    if not cpu_name:
        cpu_name = platform.processor() or "Generic Multi-Core Processor"

    return cpu_name, physical_cores, logical_cores


def get_ram_total_gb() -> float:
    """Returns total system RAM in GB."""
    if HAS_PSUTIL:
        try:
            return round(psutil.virtual_memory().total / (1024 ** 3), 2)
        except Exception:
            pass
            
    system = platform.system()
    if system == "Linux" and os.path.exists("/proc/meminfo"):
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb / (1024 * 1024), 2)
        except Exception:
            pass
    elif system == "Darwin":
        mem_str = _run_cmd(["sysctl", "-n", "hw.memsize"])
        if mem_str.isdigit():
            return round(int(mem_str) / (1024 ** 3), 2)
    elif system == "Windows":
        mem_str = _run_cmd(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"])
        if mem_str.isdigit():
            return round(int(mem_str) / (1024 ** 3), 2)

    return 8.0  # Safe generic fallback


def get_primary_storage_gb() -> float:
    """Returns total size of the primary storage drive in GB."""
    try:
        # Check root or cwd drive
        drive_path = "C:\\" if platform.system() == "Windows" else "/"
        if not os.path.exists(drive_path):
            drive_path = "."
        total, used, free = shutil.disk_usage(drive_path)
        return round(total / (1024 ** 3), 1)
    except Exception:
        return 256.0


def get_oem_details() -> tuple[str, str, Optional[str]]:
    """Returns (manufacturer, model, bios_version)."""
    system = platform.system()
    manufacturer = "Generic OEM"
    model = "Generic System"
    bios = None

    if system == "Windows":
        mfg = _run_cmd(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).Manufacturer"])
        mdl = _run_cmd(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).Model"])
        bio = _run_cmd(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion"])
        if mfg: manufacturer = mfg
        if mdl: model = mdl
        if bio: bios = bio
    elif system == "Darwin":
        manufacturer = "Apple Inc."
        model = _run_cmd(["sysctl", "-n", "hw.model"]) or "Mac"
    else:
        # Linux DMI
        sys_vendor = "/sys/class/dmi/id/sys_vendor"
        product_name = "/sys/class/dmi/id/product_name"
        bios_version = "/sys/class/dmi/id/bios_version"
        try:
            if os.path.exists(sys_vendor):
                with open(sys_vendor, "r") as f:
                    manufacturer = f.read().strip()
            if os.path.exists(product_name):
                with open(product_name, "r") as f:
                    model = f.read().strip()
            if os.path.exists(bios_version):
                with open(bios_version, "r") as f:
                    bios = f.read().strip()
        except Exception:
            pass

    return manufacturer, model, bios


def collect_system_specs() -> SystemSpecs:
    """Collects and returns comprehensive SystemSpecs."""
    os_name, os_version = get_os_details()
    cpu_name, phys_cores, log_threads = get_cpu_info()
    ram_gb = get_ram_total_gb()
    storage_gb = get_primary_storage_gb()
    mfg, mdl, bios = get_oem_details()
    arch = platform.machine() or "x86_64"

    return SystemSpecs(
        os=os_name,
        osVersion=os_version,
        cpu=cpu_name,
        cpuCores=phys_cores,
        cpuThreads=log_threads,
        ramGb=ram_gb,
        storageGb=storage_gb,
        model=mdl,
        manufacturer=mfg,
        architecture=arch,
        biosVersion=bios
    )
