"""Terminal styling, ANSI color codes, and progress bars for BenchQC."""

import sys
import os
import platform

# ANSI Escape Sequences
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright Foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def enable_windows_ansi() -> None:
    """Enables virtual terminal processing on Windows consoles if needed."""
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # STD_OUTPUT_HANDLE = -11
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


def print_banner() -> None:
    enable_windows_ansi()
    c = Colors
    banner = f"""
{c.BRIGHT_CYAN}{c.BOLD}================================================================================{c.RESET}
{c.BRIGHT_BLUE}{c.BOLD}    ____                  __    ____  ______ {c.RESET}  {c.BRIGHT_WHITE}{c.BOLD}Hardware Stress-Testing &{c.RESET}
{c.BRIGHT_BLUE}{c.BOLD}   / __ )___  ____  _____/ /_  / __ \\/ ____/ {c.RESET}  {c.BRIGHT_YELLOW}{c.BOLD}Battery Sustenance Suite{c.RESET}
{c.BRIGHT_BLUE}{c.BOLD}  / __  / _ \\/ __ \\/ ___/ __ \\/ / / / /      {c.RESET}  {c.DIM}v1.0.0 | Certified Verification Engine{c.RESET}
{c.BRIGHT_BLUE}{c.BOLD} / /_/ /  __/ / / / /__/ / / / /_/ / /___    {c.RESET}  {c.BRIGHT_GREEN}Student 3-4h Sustenance Benchmark{c.RESET}
{c.BRIGHT_BLUE}{c.BOLD}/_____/\\___/_/ /_/\\___/_/ /_/\\___\\_\\_____/    {c.RESET}  {c.BRIGHT_CYAN}Windows / Linux / macOS{c.RESET}
{c.BRIGHT_CYAN}{c.BOLD}================================================================================{c.RESET}
"""
    print(banner)


def render_progress_bar(percent: float, message: str = "", bar_length: int = 30) -> None:
    """Renders an inline animated terminal progress bar."""
    c = Colors
    pct = max(0.0, min(100.0, percent))
    filled_len = int(round(bar_length * pct / 100.0))
    bar = "=" * filled_len + "-" * (bar_length - filled_len)
    
    color = c.BRIGHT_CYAN
    if pct >= 100.0:
        color = c.BRIGHT_GREEN
    elif pct < 30.0:
        color = c.BRIGHT_YELLOW
        
    msg = message[:45]
    sys.stdout.write(f"\r  {color}[{bar}]{c.RESET} {c.BOLD}{pct:5.1f}%{c.RESET} | {msg:<45}")
    sys.stdout.flush()
    if pct >= 100.0:
        sys.stdout.write("\n")
        sys.stdout.flush()
