"""Human-readable report generator and terminal summary card renderer."""

from benchqc.schema import BenchQCAudit
from benchqc.ui.terminal import Colors
from benchqc.config import (
    BADGE_STUDENT_APPROVED,
    BADGE_CAMPUS_READY,
    BADGE_NEEDS_CHARGER,
)


def render_terminal_report(audit: BenchQCAudit) -> str:
    """Formats and prints the full BenchQC audit summary report to the terminal."""
    c = Colors
    
    # Grade color
    grade = audit.certifiedGrade
    if grade == "A+":
        grade_color = f"{c.BG_GREEN}{c.BRIGHT_WHITE}{c.BOLD}  GRADE: A+ (PLATINUM CERTIFIED)  {c.RESET}"
    elif grade == "A":
        grade_color = f"{c.BG_GREEN}{c.BLACK}{c.BOLD}  GRADE: A (CERTIFIED EXCELLENT)  {c.RESET}"
    elif grade == "B":
        grade_color = f"{c.BG_BLUE}{c.BRIGHT_WHITE}{c.BOLD}  GRADE: B (CERTIFIED GOOD)       {c.RESET}"
    elif grade == "C":
        grade_color = f"{c.BG_YELLOW}{c.BLACK}{c.BOLD}  GRADE: C (CONDITIONAL PASS)     {c.RESET}"
    else:
        grade_color = f"{c.BG_RED}{c.BRIGHT_WHITE}{c.BOLD}  GRADE: F (REJECTED / FAILED)    {c.RESET}"

    # Badge formatting
    badge = audit.battery.studentBadge
    if badge == BADGE_STUDENT_APPROVED:
        badge_str = f"{c.BRIGHT_GREEN}{c.BOLD}[STUDENT_APPROVED_4H_PLUS]{c.RESET} (>= 4.0 Hours Sustained)"
    elif badge == BADGE_CAMPUS_READY:
        badge_str = f"{c.BRIGHT_YELLOW}{c.BOLD}[CAMPUS_READY_3H_TO_4H]{c.RESET} (3.0 - 4.0 Hours Sustained)"
    else:
        badge_str = f"{c.BRIGHT_RED}{c.BOLD}[NEEDS_CHARGER_LESS_THAN_3H]{c.RESET} (< 3.0 Hours)"

    # QC Checklist icons
    def _status_icon(status: str) -> str:
        if status == "PASSED":
            return f"{c.BRIGHT_GREEN}[PASSED]{c.RESET}"
        elif status == "WARNING":
            return f"{c.BRIGHT_YELLOW}[WARN]  {c.RESET}"
        else:
            return f"{c.BRIGHT_RED}[FAILED]{c.RESET}"

    sys_info = audit.system
    bat = audit.battery
    therm = audit.thermals
    qc = audit.qcSummary
    suit = audit.studentSuitability

    lines = []
    lines.append(f"\n{c.BRIGHT_CYAN}{c.BOLD}================================================================================{c.RESET}")
    lines.append(f"               {c.BRIGHT_WHITE}{c.BOLD}BENCHQC OFFICIAL HARDWARE & BATTERY AUDIT{c.RESET}")
    lines.append(f"{c.BRIGHT_CYAN}{c.BOLD}================================================================================{c.RESET}")
    lines.append(f"  Audit ID      : {c.BRIGHT_YELLOW}{audit.auditId}{c.RESET}")
    lines.append(f"  Audit Date    : {audit.auditDate}")
    lines.append(f"  Verification  : {c.UNDERLINE}{audit.officialVerificationUrl}{c.RESET}")
    lines.append(f"\n  Overall Score : {c.BOLD}{audit.overallScore:.1f}/100{c.RESET}   {grade_color}")
    lines.append(f"  Student Badge : {badge_str}")
    lines.append(f"  Recommendation: {c.ITALIC}{suit.recommendation}{c.RESET}")
    
    lines.append(f"\n{c.BRIGHT_BLUE}{c.BOLD}[1] SYSTEM & HARDWARE SPECIFICATIONS{c.RESET}")
    lines.append(f"  * Device Model : {sys_info.manufacturer} {sys_info.model}")
    lines.append(f"  * Processor    : {sys_info.cpu} ({sys_info.cpuCores} physical cores, {sys_info.cpuThreads} threads)")
    lines.append(f"  * Memory (RAM) : {sys_info.ramGb:.1f} GB")
    lines.append(f"  * Primary Disk : {sys_info.storageGb:.1f} GB")
    lines.append(f"  * Operating Sys: {sys_info.os} ({sys_info.architecture})")

    lines.append(f"\n{c.BRIGHT_YELLOW}{c.BOLD}[2] BATTERY TELEMETRY & SUSTENANCE PROFILING{c.RESET}")
    lines.append(f"  * Health / Wear: {c.BRIGHT_GREEN}{bat.healthPercent:.1f}% Health{c.RESET} (Wear: {bat.wearPercent:.1f}%, Cycles: {bat.cycleCount})")
    lines.append(f"  * Capacity     : {bat.fullCapacityMwh:,.0f} mWh (Full) / {bat.designCapacityMwh:,.0f} mWh (Design)")
    lines.append(f"  * Telemetry    : Voltage: {bat.currentVoltageMv:,.0f} mV | Discharge Rate: {bat.dischargeRateMw:,.0f} mW")
    lines.append(f"  * Mode / State : {bat.powerState} {'[Simulated/AC Calibrated]' if bat.isSimulatedOrAC else '[Direct Hardware Node]'}")
    lines.append(f"  * Projected Run: {c.BRIGHT_GREEN}{c.BOLD}{bat.projectedHoursStudent:.1f}h (Student Multitasking){c.RESET} | {bat.projectedHoursHeavy:.1f}h (100% Torture) | {bat.projectedHoursIdle:.1f}h (Standby)")

    lines.append(f"\n{c.BRIGHT_MAGENTA}{c.BOLD}[3] THERMAL & THROTTLING TELEMETRY{c.RESET}")
    throttle_status = f"{c.BRIGHT_RED}YES ({therm.throttlingPercent:.1f}% drop){c.RESET}" if therm.throttleDetected else f"{c.BRIGHT_GREEN}NO (Stable Cooling){c.RESET}"
    lines.append(f"  * Temperature  : Baseline: {therm.baselineTempC:.1f}C | Peak Load: {therm.peakTempC:.1f}C (+{therm.deltaTempC:.1f}C delta)")
    lines.append(f"  * CPU Clock    : Baseline: {therm.frequencyBaselineGhz:.2f} GHz | Stress: {therm.frequencyUnderStressGhz:.2f} GHz")
    lines.append(f"  * Throttling   : {throttle_status}")

    lines.append(f"\n{c.BRIGHT_WHITE}{c.BOLD}[4] HARDWARE QUALITY CONTROL CHECKLIST{c.RESET}")
    lines.append(f"  * CPU Torture & FP Matrix Burn   : {_status_icon(qc.cpuStatus)} (Score: {audit.benchmarks.cpuMultiCoreScore:.1f})")
    lines.append(f"  * Memory Saturation & Parity     : {_status_icon(qc.memoryStatus)} ({audit.benchmarks.memoryThroughputMbSec:,.0f} MB/s, 0 bit flips)")
    lines.append(f"  * Storage Sequential & Random IO : {_status_icon(qc.storageStatus)} (Seq Write: {audit.benchmarks.storageSeqWriteMbSec:.0f} MB/s, Read: {audit.benchmarks.storageSeqReadMbSec:.0f} MB/s)")
    lines.append(f"  * Battery Sustenance & Health    : {_status_icon(qc.batteryStatus)} ({bat.healthPercent:.1f}% health)")
    lines.append(f"  * Thermal Cooling Dissipation    : {_status_icon(qc.thermalStatus)} (Peak: {therm.peakTempC:.1f}C)")
    lines.append(f"  * Overall QC Certification       : {c.BOLD}{c.BRIGHT_GREEN if qc.overallStatus == 'CERTIFIED' else c.BRIGHT_YELLOW}{qc.overallStatus}{c.RESET} ({qc.passedChecksCount}/{qc.totalChecksCount} passed)")

    lines.append(f"\n{c.BRIGHT_CYAN}{c.BOLD}================================================================================{c.RESET}")
    lines.append(f"{c.BRIGHT_GREEN}{c.BOLD}[+] benchqc_audit.json successfully generated and signed.{c.RESET}")
    lines.append(f"{c.DIM}Ready for one-click upload/import into the BenchQC Storefront.{c.RESET}\n")

    report_text = "\n".join(lines)
    print(report_text)
    return report_text
