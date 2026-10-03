===============================================================================
     BENCHQC HARDWARE STRESS-TESTING & BATTERY SUSTENANCE SUITE (USB EDITION)
===============================================================================

Plug this USB into any laptop to stress test hardware, measure battery health,
evaluate student campus endurance (3-4+ hours), and generate a verified HTML certificate.

QUICK START INSTRUCTIONS:
-------------------------------------------------------------------------------
1. FOR WINDOWS LAPTOPS:
   - Double-click "run_windows_quick.bat"   -> Fast 10-second intake check.
   - Double-click "run_windows.bat"         -> Full standard student certification.
   - Double-click "run_windows_heavy.bat"   -> Maximum 100% heavy torture test (45s).
   
   * Once finished, it automatically opens "benchqc_report.html" in your browser!

2. FOR LINUX LAPTOPS:
   - Open a terminal in this folder and run:
     ./run_linux.sh
   - For maximum heavy test:
     ./run_linux.sh --heavy

3. FOR APPLE MAC (macOS):
   - Open Terminal in this folder and run:
     ./run_mac.sh
   - For maximum heavy test:
     ./run_mac.sh --heavy

OUTPUT FILES GENERATED IN THIS FOLDER:
-------------------------------------------------------------------------------
- benchqc_report.html : Self-contained visual certificate with interactive battery
                        gauge, 3-tier runtime projections, and hardware specs.
                        (Double-click anytime to open in Chrome/Edge/Firefox/Safari).
- benchqc_audit.json  : Standard diagnostic JSON artifact ready to drag & drop
                        into the BenchQC Storefront Retailer Intake Studio.

STUDENT BATTERY BADGES:
-------------------------------------------------------------------------------
[STUDENT_APPROVED_4H_PLUS] -> Sustains >= 4.0 hours of active multitasking.
[CAMPUS_READY_3H_TO_4H]    -> Sustains 3.0 to 4.0 hours of lecture work.
[NEEDS_CHARGER_LESS_THAN_3H] -> Sustains < 3.0 hours (requires charger).
===============================================================================
