#!/usr/bin/env python3
"""BookForge CLI Entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import shutil

from bookforge.core import validator as context_validator
from bookforge.core import loop as loop_controller
from bookforge.core import compiler as compiler_module
from bookforge.core import scanner as scanner_module
from bookforge.core import rhythm as rhythm_module
from bookforge.core import chain as chain_module
from bookforge import config


def cmd_init(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if book_folder.exists() and any(book_folder.iterdir()):
        print(f"Error: Directory '{book_folder}' already exists and is not empty.", file=sys.stderr)
        return 1

    book_folder.mkdir(parents=True, exist_ok=True)
    
    # Source files to create
    template_files = {
        "phase-0.md": "phase-0.md",
        "rulebook.md": "rulebook.md",
        "mood-lock.md": "mood-lock.md",
        "chapter-summaries.md": "chapter-summaries.md"
    }

    src_templates_dir = config.DEFAULT_TEMPLATES_DIR
    book_example_dir = config.DEFAULT_BOOK_EXAMPLE_DIR

    for filename, dest_name in template_files.items():
        dest_path = book_folder / dest_name
        # 1. Try to copy from default example first
        src_example = book_example_dir / filename
        if src_example.exists():
            shutil.copy2(src_example, dest_path)
            print(f"Created: {dest_path} (copied from example)")
            continue

        # 2. Try to copy from templates
        src_template = src_templates_dir / filename
        if src_template.exists():
            shutil.copy2(src_template, dest_path)
            print(f"Created: {dest_path} (copied from template)")
            continue

        # 3. Fallback stub
        dest_path.write_text(f"# {book_folder.name.replace('-', ' ').title()}\n\nStub file for {filename}.\n", encoding="utf-8")
        print(f"Created: {dest_path} (fallback stub)")

    # Create chapters structure stub
    chapters_dir = book_folder / "chapters"
    chapters_dir.mkdir(exist_ok=True)
    
    print(f"\nSuccessfully initialized book pipeline in: '{book_folder}'")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    print(f"=== BookForge Status for {book_folder.name} ===\n")

    # 1. Required files and validation reports
    book_passes, book_failures = context_validator.validate_required_book_files(book_folder)
    print("Files Validation:")
    for p in book_passes:
        print(f"  [PASS] {p}")
    for f in book_failures:
        print(f"  [FAIL] {f}")
    
    # 2. Chapter gaps check
    failures, warnings = scanner_module.check_gaps(book_folder)
    print("\nStructure gaps check:")
    if not failures and not warnings:
        print("  [PASS] No gaps or unexpected directories.")
    else:
        for f in failures:
            print(f"  [FAIL] {f}")
        for w in warnings:
            print(f"  [WARN] {w}")

    # 3. Continuity chain check
    passed_chain, chain_logs = chain_module.analyze_chain(book_folder)
    print("\nContinuity Chain:")
    if passed_chain:
        print("  [PASS] Continuity chain is unbroken.")
    else:
        print("  [FAIL] Unresolved continuity issues:")
        for log in chain_logs:
            print(f"    - {log}")

    # 4. Rhythm check
    try:
        rhythm_report = rhythm_module.analyze(book_folder)
        print("\nChapter Rhythm:")
        if rhythm_report.issues:
            for issue in rhythm_report.issues:
                print(f"  [{issue.level}] {issue.message}")
        else:
            print("  [PASS] Chapter rhythm variance is healthy.")
    except Exception as e:
        print(f"\nChapter Rhythm: [WARN] Could not analyze rhythm ({e})")

    print("\nRun 'bf run-loop <book_folder>' to see the next workflow action.")
    return 0


def cmd_run_loop(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    # Parse attempts
    cli_attempts = {}
    if args.repair_attempt:
        for pair in args.repair_attempt.split(","):
            if ":" in pair:
                slug, val = pair.split(":", 1)
                try:
                    cli_attempts[slug] = int(val)
                except ValueError:
                    pass

    status, reason, report_text = loop_controller.run_loop_check(
        book_folder=book_folder,
        target_min=args.target_min,
        target_max=args.target_max,
        cli_attempts=cli_attempts,
        max_repair_attempts=args.max_repair_attempts
    )

    print(report_text)
    return 2 if status == "BLOCKED" else 0


def cmd_compile(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    output_path = Path(args.output) if args.output else book_folder / compiler_module.DEFAULT_OUTPUT_NAME

    try:
        draft_count, word_count = compiler_module.compile_manuscript(
            book_folder=book_folder,
            output_path=output_path,
            include_title=not args.no_title,
        )
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print("# Manuscript Compile Report")
    print("")
    print(f"- **Book Folder:** `{book_folder}`")
    print(f"- **Output:** `{output_path}`")
    print(f"- **Draft Files Compiled:** {draft_count}")
    print(f"- **Compiled Words:** {word_count}")
    return 0


def cmd_tui(args: argparse.Namespace) -> int:
    from bookforge.tui import BookForgeTUI
    tui = BookForgeTUI()
    tui.run()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BookForge: A Production-Ready Manuscript Workflow Pipeline",
        prog="bookforge"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    parser_init = subparsers.add_parser("init", help="Initialize a new book structure")
    parser_init.add_argument("book_folder", help="Path to book folder (e.g. books/my-book)")

    # status
    parser_status = subparsers.add_parser("status", help="Show pipeline diagnostics and validations")
    parser_status.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")

    # run-loop
    parser_run = subparsers.add_parser("run-loop", help="Check loop state and print next action")
    parser_run.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")
    parser_run.add_argument("--target-min", type=int, help="Target minimum words")
    parser_run.add_argument("--target-max", type=int, help="Target maximum words")
    parser_run.add_argument("--repair-attempt", help="Comma-separated repair overrides (e.g. chapter-01:3)")
    parser_run.add_argument("--max-repair-attempts", type=int, default=3, help="Max repair attempts allowed")

    # compile
    parser_compile = subparsers.add_parser("compile", help="Compile drafts into single manuscript")
    parser_compile.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")
    parser_compile.add_argument("--output", help="Output Markdown path")
    parser_compile.add_argument("--no-title", action="store_true", help="Do not prepend book title")

    # tui
    subparsers.add_parser("tui", help="Launch interactive Terminal User Interface (TUI)")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "status": cmd_status,
        "run-loop": cmd_run_loop,
        "compile": cmd_compile,
        "tui": cmd_tui,
    }

    try:
        return commands[args.command](args)
    except Exception as e:
        print(f"Execution Error: {e}", file=sys.stderr)
        return 1




if __name__ == "__main__":
    sys.exit(main())
