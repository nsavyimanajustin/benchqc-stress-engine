"""Command-line interface for the BenchQC Stress Engine."""

import sys
import os
import argparse
from benchqc.version import VERSION, APP_NAME
from benchqc.config import BenchConfig
from benchqc.engine import BenchQCEngine
from benchqc.ui.terminal import print_banner, Colors
from benchqc.ui.report import render_terminal_report


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} (v{VERSION})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m benchqc                     # Run full standard hardware audit & battery sustenance profiling
  python -m benchqc --quick             # Run fast intake validation audit (5-10s)
  python -m benchqc -o my_audit.json    # Save audit artifact to custom JSON path
  python -m benchqc --battery-only      # Run only the Student Sustenance Battery Benchmark
        """
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Run quick intake audit mode (shortened stress and sampling times)."
    )
    parser.add_argument(
        "--heavy", "-H",
        action="store_true",
        help="Run maximum heavy stress test (sustained 100% CPU burn, large RAM fill, deep I/O torture)."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="benchqc_audit.json",
        help="Path for output JSON audit artifact (default: benchqc_audit.json)."
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress ASCII art header."
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Suppress human-readable terminal report (outputs only JSON)."
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"{APP_NAME} v{VERSION}"
    )
    return parser.parse_args(args)


def main(argv=None) -> int:
    args = parse_args(argv)

    if not args.no_banner:
        print_banner()

    if args.heavy:
        print(f"  {Colors.BRIGHT_RED}[i] Running in MAXIMUM HEAVY STRESS mode (--heavy active)...{Colors.RESET}\n")
        cfg = BenchConfig.heavy()
    elif args.quick:
        print(f"  {Colors.BRIGHT_YELLOW}[i] Running in QUICK AUDIT mode (--quick active)...{Colors.RESET}\n")
        cfg = BenchConfig.quick()
    else:
        print(f"  {Colors.BRIGHT_CYAN}[i] Running in FULL STANDARD AUDIT mode...{Colors.RESET}\n")
        cfg = BenchConfig.standard()

    engine = BenchQCEngine(config=cfg)

    try:
        audit = engine.run_full_suite(output_file=args.output)
        
        if not args.no_report:
            render_terminal_report(audit)

        return 0
    except KeyboardInterrupt:
        print(f"\n{Colors.BRIGHT_RED}[!] Audit aborted by user.{Colors.RESET}")
        return 130
    except Exception as e:
        print(f"\n{Colors.BRIGHT_RED}[ERROR] Engine encountered fatal error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
