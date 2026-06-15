#!/usr/bin/env python3
"""BookForge Terminal User Interface (TUI) Core Module."""

from __future__ import annotations

import os
import sys
import tty
import termios
import re
from pathlib import Path

from bookforge.core import validator, loop, length, rhythm, compiler, scanner, chain, series

# ANSI escape codes for styling
CLEAR_SCREEN = "\033[H\033[J"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

COLOR_BLUE = "\033[94m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"
COLOR_MAGENTA = "\033[95m"
COLOR_GRAY = "\033[90m"

BG_CYAN = "\033[46m\033[30m"
BG_BLUE = "\033[44m\033[37m"


def get_key() -> str:
    """Reads a single keypress from standard input without blocking echo."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            # Check for arrow keys
            ch2 = sys.stdin.read(1)
            ch3 = sys.stdin.read(1)
            if ch2 == "[":
                if ch3 == "A":
                    return "up"
                elif ch3 == "B":
                    return "down"
                elif ch3 == "C":
                    return "right"
                elif ch3 == "D":
                    return "left"
            return "esc"
        elif ch == "\r" or ch == "\n":
            return "enter"
        elif ch == "\x7f" or ch == "\x08":
            return "backspace"
        elif ch == "\x03":  # Ctrl+C
            raise KeyboardInterrupt()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch.lower()


def discover_books(root_dir: Path = Path("books")) -> list[Path]:
    """Finds all book folders that contain a source outline format file, supporting nested series subfolders."""
    if not root_dir.exists():
        return []
    books = []
    for item in sorted(root_dir.iterdir()):
        if item.is_dir():
            # Check if any source files exist in the immediate directory
            if any((item / name).exists() for name in scanner.SOURCE_NAMES):
                books.append(item)
            else:
                # Check 1 level deeper for series subfolders
                for subitem in sorted(item.iterdir()):
                    if subitem.is_dir() and any((subitem / name).exists() for name in scanner.SOURCE_NAMES):
                        books.append(subitem)
    return books


class BookForgeTUI:
    def __init__(self):
        self.books = discover_books()
        self.selected_index = 0
        self.current_book: Path | None = None
        self.state = "BOOK_LIST"  # BOOK_LIST, DASHBOARD, RUNNING_CMD
        self.status_cache: dict[str, any] = {}

    def draw_header(self, subtitle: str = "") -> None:
        """Renders the top banner of the BookForge TUI."""
        width = 70
        title = " BookForge Studio "
        padding = (width - len(title)) // 2
        
        print(CLEAR_SCREEN)
        print(f"{COLOR_BLUE}{BOLD}{'=' * width}{RESET}")
        print(f"{COLOR_BLUE}{BOLD}{' ' * padding}{title}{' ' * padding}{RESET}")
        print(f"{COLOR_BLUE}{BOLD}{'=' * width}{RESET}")
        if subtitle:
            print(f"  {COLOR_CYAN}{BOLD}{subtitle}{RESET}\n")
        else:
            print()

    def run(self) -> None:
        """Main TUI loop."""
        # Save terminal state, hide cursor, and set clean screen exits
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.flush()
        try:
            while True:
                if self.state == "BOOK_LIST":
                    self.render_book_list()
                    key = get_key()
                    self.handle_book_list_key(key)
                elif self.state == "DASHBOARD":
                    self.render_dashboard()
                    key = get_key()
                    self.handle_dashboard_key(key)
                elif self.state == "ANALYTICS":
                    self.render_analytics()
                    key = get_key()
                    self.handle_analytics_key(key)
                else:
                    # Fallback
                    self.state = "BOOK_LIST"
        except KeyboardInterrupt:
            pass
        finally:
            # Show cursor and restore normal terminal state
            sys.stdout.write("\033[?25h" + CLEAR_SCREEN)
            sys.stdout.flush()

    def render_book_list(self) -> None:
        self.draw_header("Select a Book Project")
        if not self.books:
            print(f"  {COLOR_RED}No books found in 'books/' directory.{RESET}")
            print(f"  Please make sure your outline source files exist (e.g. phase-0.md).")
            print(f"\n  Press {BOLD}[q]{RESET} to quit.")
            return

        print(f"  Navigate with {COLOR_CYAN}Arrow Keys{RESET} and press {COLOR_CYAN}Enter{RESET} to select:\n")
        
        for idx, book in enumerate(self.books):
            series_info = series.get_series_info(book)
            series_prefix = f"[{series_info['name']}] " if series_info else ""

            title = book.name
            # Attempt to read title from phase-0.md
            outline_path = scanner.source_path(book)
            if outline_path:
                try:
                    content = outline_path.read_text(encoding="utf-8")
                    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if title_match:
                        title = f"{title_match.group(1).strip()} ({book.name})"
                except Exception:
                    pass

            display_title = f"{series_prefix}{title}"
            if idx == self.selected_index:
                print(f"  {BG_CYAN} > {display_title:<60} {RESET}")
            else:
                print(f"    - {title}")

        print(f"\n  {COLOR_GRAY}{'─' * 66}{RESET}")
        print(f"  {BOLD}[q]{RESET} Quit")

    def handle_book_list_key(self, key: str) -> None:
        if key == "q":
            raise KeyboardInterrupt()
        elif key == "up":
            self.selected_index = max(0, self.selected_index - 1)
        elif key == "down":
            self.selected_index = min(len(self.books) - 1, self.selected_index + 1)
        elif key == "enter" and self.books:
            self.current_book = self.books[self.selected_index]
            self.state = "DASHBOARD"
            self.status_cache = {}  # Reset cache for new book

    def render_dashboard(self) -> None:
        assert self.current_book is not None
        book_folder = self.current_book
        series_info = series.get_series_info(book_folder)
        header_title = f"Dashboard: {book_folder.name}"
        if series_info:
            header_title = f"[{series_info['name']}] {header_title}"
        self.draw_header(header_title)

        # If status check hasn't run yet, offer to run it
        if "gaps" not in self.status_cache:
            print(f"  {COLOR_YELLOW}Press [s] to run project status and validation checks.{RESET}\n")
        else:
            # Render cached results
            gaps_fail, gaps_warn = self.status_cache["gaps"]
            len_state = self.status_cache["length"]
            chain_ok, chain_logs = self.status_cache["chain"]

            # 1. Structure Check
            print(f"  {BOLD}1. Folder Structure & Gaps:{RESET}")
            if gaps_fail:
                print(f"     Status: {COLOR_RED}FAIL{RESET}")
                for f in gaps_fail[:3]:
                    print(f"       - {f}")
            elif gaps_warn:
                print(f"     Status: {COLOR_YELLOW}WARNING{RESET}")
                for w in gaps_warn[:3]:
                    print(f"       - {w}")
            else:
                print(f"     Status: {COLOR_GREEN}PASS{RESET}")

            # 2. Length check
            print(f"\n  {BOLD}2. Word Count Status:{RESET}")
            if len_state:
                prog = len_state.total_words
                t_min = len_state.target_min
                t_max = len_state.target_max
                bar_len = 30
                if t_max > 0:
                    pct = min(1.0, prog / t_max)
                    filled = int(pct * bar_len)
                    bar = f"[{'#' * filled}{'-' * (bar_len - filled)}]"
                else:
                    bar = ""
                
                print(f"     Words: {COLOR_CYAN}{prog:,}{RESET} / target min {t_min:,} {bar}")
                if prog < t_min:
                    print(f"     Status: {COLOR_YELLOW}NEEDS EXPANSION{RESET} (remaining: {t_min - prog:,} words)")
                elif prog > t_max:
                    print(f"     Status: {COLOR_YELLOW}OVER MAX TARGET{RESET} (limit: {t_max:,})")
                else:
                    print(f"     Status: {COLOR_GREEN}PASS{RESET}")

            # 3. Continuity Chain
            print(f"\n  {BOLD}3. Continuity Chain:{RESET}")
            if not chain_ok:
                print(f"     Status: {COLOR_RED}FAIL{RESET}")
                for err in chain_logs[:3]:
                    print(f"       - {err}")
            else:
                print(f"     Status: {COLOR_GREEN}PASS{RESET}")

            # 4. World State & Physical Logistics
            print(f"\n  {BOLD}4. World State & Physical Logistics:{RESET}")
            try:
                from bookforge.core import world as world_module
                world_state = world_module.load_world_state(book_folder)
                characters = world_state.get("characters", {})
                if not characters:
                    print("     Status: No character status registered.")
                else:
                    locs = []
                    for char, info in characters.items():
                        status_marker = " [DEAD]" if info.get("status") == "dead" else ""
                        locs.append(f"{char.capitalize()}{status_marker} at '{info.get('location', 'unknown')}'")
                    print(f"     Locations: {', '.join(locs)}")
                    
                    invs = []
                    for char, info in characters.items():
                        if info.get("status") != "dead":
                            items = info.get("inventory", [])
                            invs.append(f"{char.capitalize()}: {items}")
                    if invs:
                        print(f"     Inventory: {'; '.join(invs)}")
            except Exception as e:
                print(f"     Status: {COLOR_RED}Error loading logistics: {e}{RESET}")

        # Fetch and render the status line
        from bookforge.core import analytics as analytics_module
        from bookforge.core import persona as persona_module
        analytics_data = analytics_module.load_analytics(book_folder)
        model_str = analytics_data.get("last_model_used", "unknown")
        total_in = analytics_data.get("total_input_tokens", 0)
        total_out = analytics_data.get("total_output_tokens", 0)
        total_runs = analytics_data.get("total_runs", 0)
        cumulative_cost = persona_module.calculate_cumulative_cost(book_folder)
        
        print(f"\n  {BG_BLUE} Model: {model_str:<12} | Cost: ${cumulative_cost:.4f} | Tokens: {total_in + total_out:,} ({total_in:,} In / {total_out:,} Out) | Runs: {total_runs:<3} {RESET}")

        print(f"  {COLOR_GRAY}{'─' * 66}{RESET}")
        print(f"  {BOLD}[s]{RESET} Run Validation   {BOLD}[l]{RESET} Run Loop   {BOLD}[c]{RESET} Compile Manuscript")
        print(f"  {BOLD}[a]{RESET} View Analytics    {BOLD}[b]{RESET} Back to list      {BOLD}[q]{RESET} Quit")

    def handle_dashboard_key(self, key: str) -> None:
        assert self.current_book is not None
        if key == "q":
            raise KeyboardInterrupt()
        elif key == "a":
            self.state = "ANALYTICS"
        elif key == "b":
            self.state = "BOOK_LIST"
        elif key == "s":
            # Run validation checks
            sys.stdout.write("\033[?25h")  # Show cursor for command execution
            print(f"\nRunning validation checks on {self.current_book.name}...")
            
            # Gaps
            gaps_fail, gaps_warn = scanner.check_gaps(self.current_book)
            
            # Length
            src = scanner.source_path(self.current_book)
            len_state = None
            if src:
                outline_text = src.read_text(encoding="utf-8")
                target = scanner.first_target(outline_text)
                target_words = target[0] if target else 30000
                len_state = loop.build_length_state(self.current_book, target_words, target_words + 1000)
            
            # Chain
            chain_ok, chain_logs = chain.analyze_chain(self.current_book)
            
            self.status_cache = {
                "gaps": (gaps_fail, gaps_warn),
                "length": len_state,
                "chain": (chain_ok, chain_logs)
            }
            sys.stdout.write("\033[?25l")  # Hide cursor again
        elif key == "l":
            sys.stdout.write("\033[?25h")  # Show cursor
            print(CLEAR_SCREEN)
            width = 70
            print(f"{COLOR_BLUE}{BOLD}{'=' * width}{RESET}")
            print(f"{COLOR_BLUE}{BOLD} Starting Autonomous Loop: {self.current_book.name} {RESET}")
            print(f"{COLOR_BLUE}{BOLD}{'=' * width}{RESET}\n")
            print("  Press Ctrl+C to cancel loop execution at any time.\n")
            
            # Retrieve target words
            src = scanner.source_path(self.current_book)
            target_words = 30000
            if src:
                try:
                    outline_text = src.read_text(encoding="utf-8")
                    target = scanner.first_target(outline_text)
                    if target:
                        target_words = target[0]
                except Exception:
                    pass
            
            try:
                status, reason, report = loop.run_loop_check(
                    book_folder=self.current_book,
                    target_min=target_words,
                    target_max=target_words + 1000
                )
                self.print_colorized_report(report)
            except KeyboardInterrupt:
                print(f"\n  {COLOR_YELLOW}Loop execution cancelled by user.{RESET}")
            except Exception as e:
                print(f"\n  {COLOR_RED}Error running loop: {e}{RESET}")
            
            print(f"\n  {COLOR_GRAY}{'─' * 66}{RESET}")
            print("  Press any key to return to Dashboard...")
            get_key()
            sys.stdout.write("\033[?25l")  # Hide cursor
        elif key == "c":
            sys.stdout.write("\033[?25h")
            print(CLEAR_SCREEN)
            width = 70
            print(f"{COLOR_BLUE}{BOLD}{'=' * width}{RESET}")
            print(f"{COLOR_BLUE}{BOLD} Compiling Manuscript: {self.current_book.name} {RESET}")
            print(f"{COLOR_BLUE}{BOLD}{'=' * width}{RESET}\n")
            
            output_path = self.current_book / "manuscript.md"
            try:
                draft_count, word_count = compiler.compile_manuscript(
                    book_folder=self.current_book,
                    output_path=output_path,
                    include_title=True
                )
                print(f"  {COLOR_GREEN}{BOLD}✔ Compile Successful!{RESET}")
                print(f"  {COLOR_GRAY}•{RESET} Draft Files: {COLOR_CYAN}{draft_count}{RESET}")
                print(f"  {COLOR_GRAY}•{RESET} Total Words: {COLOR_CYAN}{word_count:,}{RESET}")
                print(f"  {COLOR_GRAY}•{RESET} Output File: {COLOR_CYAN}{output_path}{RESET}")
            except Exception as e:
                print(f"  {COLOR_RED}{BOLD}✘ Compile Failed!{RESET}")
                print(f"  {COLOR_RED}  Error: {e}{RESET}")
                
            print(f"\n  {COLOR_GRAY}{'─' * 66}{RESET}")
            print("  Press any key to return to Dashboard...")
            get_key()
            sys.stdout.write("\033[?25l")

    def print_colorized_report(self, report_text: str) -> None:
        """Helper to output loop reports using standard-library colorization."""
        for line in report_text.splitlines():
            line_strip = line.strip()
            if line.startswith("# "):
                print(f"  {COLOR_BLUE}{BOLD}{line[2:].replace('**', '')}{RESET}")
            elif line.startswith("## "):
                print(f"\n  {COLOR_CYAN}{BOLD}{line[3:].replace('**', '')}{RESET}")
            elif line_strip.startswith("- **Status:**"):
                status = line_strip.split(":", 1)[1].replace("**", "").strip()
                color = COLOR_GREEN
                if "BLOCKED" in status or "STOP" in status:
                    color = COLOR_RED
                elif "EXPANSION" in status or "WARN" in status:
                    color = COLOR_YELLOW
                print(f"  {BOLD}• Status:{RESET} {color}{status}{RESET}")
            elif line_strip.startswith("- **Decision:**"):
                dec = line_strip.split(":", 1)[1].replace("**", "").strip()
                color = COLOR_GREEN if "CONTINUE" in dec else COLOR_RED
                print(f"  {BOLD}• Decision:{RESET} {color}{dec}{RESET}")
            elif line_strip.startswith("- **Reason:**"):
                reason = line_strip.split(":", 1)[1].replace("**", "").strip()
                print(f"  {BOLD}• Reason:{RESET} {reason}")
            elif line_strip.startswith("- **Prompt Mode:**"):
                mode = line_strip.split(":", 1)[1].replace("**", "").strip()
                print(f"  {BOLD}• Prompt Mode:{RESET} {COLOR_MAGENTA}{mode}{RESET}")
            elif line_strip.startswith("- **Next Action:**"):
                action = line_strip.split(":", 1)[1].replace("**", "").strip()
                print(f"  {BOLD}• Next Action:{RESET} {COLOR_YELLOW}{action}{RESET}")
            elif line_strip.startswith("- **Current Words:**"):
                parts = line_strip.split(":", 1)[1].replace("**", "").strip()
                match = re.search(r"(\d+)\s*/\s*(?:Min target|target min)[\s:]*(\d+)", parts, re.IGNORECASE)
                if match:
                    prog = int(match.group(1))
                    t_min = int(match.group(2))
                    bar_len = 30
                    pct_val = min(1.0, prog / t_min) if t_min > 0 else 0
                    filled = int(pct_val * bar_len)
                    bar = f"[{'#' * filled}{'-' * (bar_len - filled)}]"
                    print(f"  {BOLD}• Word Count:{RESET} {COLOR_CYAN}{prog:,}{RESET} / target min {t_min:,} {bar}")
                else:
                    print(f"  {BOLD}• Word Count:{RESET} {COLOR_CYAN}{parts}{RESET}")
            elif line_strip.startswith("- "):
                clean_item = line_strip[2:].replace("**", "")
                print(f"  {COLOR_GRAY}•{RESET} {clean_item}")
            else:
                print(f"  {line}")

    def render_analytics(self) -> None:
        assert self.current_book is not None
        book_folder = self.current_book
        self.draw_header(f"Project Analytics: {book_folder.name}")

        from bookforge.core import analytics as analytics_module
        file_analytics = analytics_module.get_project_file_analytics(book_folder)
        analytics_data = analytics_module.load_analytics(book_folder)

        print(f"  {BOLD}Cumulative API Token Stats:{RESET}")
        print(f"    • Total runs logged: {COLOR_CYAN}{analytics_data['total_runs']}{RESET}")
        print(f"    • Active/Last Model: {COLOR_CYAN}{analytics_data['last_model_used']}{RESET}")
        print(f"    • Total Tokens:      {COLOR_CYAN}{analytics_data['total_input_tokens'] + analytics_data['total_output_tokens']:,}{RESET} ({analytics_data['total_input_tokens']:,} In / {analytics_data['total_output_tokens']:,} Out)")
        print()

        print(f"  {BOLD}Individual File Metrics:{RESET}")
        print(f"    {COLOR_GRAY}{'─' * 62}{RESET}")
        print(f"    {COLOR_CYAN}{'File':<30} | {'Lines':<5} | {'Words':<6} | {'Tokens':<6}{RESET}")
        print(f"    {COLOR_GRAY}{'─' * 62}{RESET}")

        for name in ["outline", "rulebook", "mood_lock", "chapter_summaries", "research_pack"]:
            if name in file_analytics:
                f = file_analytics[name]
                m = f["metrics"]
                print(f"    {f['filename']:<30} | {m['lines']:<5} | {m['words']:<6} | {m['tokens']:<6}")

        for chap in file_analytics.get("chapters", []):
            for f_key in ["scene_breakdown", "draft", "continuity_out"]:
                if f_key in chap["files"]:
                    f = chap["files"][f_key]
                    m = f["metrics"]
                    path_label = f"{chap['slug']}/{f['filename']}"
                    if len(path_label) > 30:
                        path_label = path_label[:27] + "..."
                    print(f"    {path_label:<30} | {m['lines']:<5} | {m['words']:<6} | {m['tokens']:<6}")

        print(f"\n  {COLOR_GRAY}{'─' * 66}{RESET}")
        print(f"  {BOLD}[b]{RESET} Back to Dashboard   {BOLD}[q]{RESET} Quit")

    def handle_analytics_key(self, key: str) -> None:
        if key == "q":
            raise KeyboardInterrupt()
        elif key == "b":
            self.state = "DASHBOARD"

