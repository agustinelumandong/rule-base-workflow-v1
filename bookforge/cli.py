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
from bookforge.core import analytics as analytics_module
from bookforge.core import series as series_module
from bookforge.core import action as action_module
from bookforge.core import persona as persona_module
from bookforge.core import repair as repair_module
from bookforge.core import relationship as relationship_module
from bookforge.core import research as research_module
from bookforge.core import pacing as pacing_module
from bookforge.core import packet as packet_module
from bookforge.core import characters as characters_module
from bookforge import config


BOOKS_ROOT = Path("books")
BOOK_COMPATIBILITY_MARKERS = {
    "phase-0.md",
    "phase-00.md",
    "outline.md",
    "chapter-outline.md",
    "source-format-scan.md",
    "rulebook.md",
    "mood-lock.md",
    "chapter-summaries.md",
    "manuscript.md",
    "compiled-manuscript.md",
    "loop-state.json",
    "world-state.json",
    "chapters",
    "characters",
    "spec",
    "canon",
}


def _normalize_init_book_folder(raw_book_folder: str) -> Path:
    requested = Path(raw_book_folder)
    if requested.is_absolute():
        try:
            return BOOKS_ROOT / requested.relative_to((Path.cwd() / BOOKS_ROOT).resolve())
        except ValueError:
            return BOOKS_ROOT / requested.name
    if requested.parts and requested.parts[0] == BOOKS_ROOT.name:
        return requested
    return BOOKS_ROOT / requested.name


def _is_compatible_book_folder(book_folder: Path) -> bool:
    if not book_folder.exists() or not any(book_folder.iterdir()):
        return True
    return any((book_folder / marker).exists() for marker in BOOK_COMPATIBILITY_MARKERS)


def _has_book_marker(book_folder: Path) -> bool:
    return any((book_folder / marker).exists() for marker in BOOK_COMPATIBILITY_MARKERS)


def _child_book_folders(book_folder: Path) -> list[Path]:
    if not book_folder.exists():
        return []
    return sorted(
        child
        for child in book_folder.iterdir()
        if child.is_dir() and _has_book_marker(child)
    )


def _normalize_books_folder_arg(raw_book_folder: str) -> Path:
    requested = Path(raw_book_folder)
    if requested.is_absolute():
        return requested
    if requested.parts and requested.parts[0] == BOOKS_ROOT.name:
        return requested
    return BOOKS_ROOT / requested


def _available_book_names() -> list[str]:
    if not BOOKS_ROOT.exists():
        return []
    return sorted(path.name for path in BOOKS_ROOT.iterdir() if path.is_dir())


def cmd_init(args: argparse.Namespace) -> int:
    book_folder = _normalize_init_book_folder(args.book_folder)
    if not _is_compatible_book_folder(book_folder):
        print(
            f"Error: Directory '{book_folder}' already exists but does not look like a BookForge book folder.",
            file=sys.stderr,
        )
        return 1

    book_folder.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy shared series resources first if book is nested in a series folder
    copied_resources = series_module.copy_shared_series_resources(book_folder)
    for res in copied_resources:
        print(res)

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
        # Skip if file was already created by shared series resources
        if dest_path.exists():
            continue

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

    character_files = characters_module.scaffold_character_files(book_folder)
    for path in character_files:
        print(f"Created: {path}")

    # 2. Perform continuity carry-forward from a completed book if requested
    if hasattr(args, "carry_from") and args.carry_from:
        carry_from_path = Path(args.carry_from)
        carry_msg = series_module.carry_forward_book_continuity(carry_from_path, book_folder)
        print(carry_msg)

    # Create local spec directory and model-routing.yml
    spec_dir = book_folder / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    model_routing_path = spec_dir / "model-routing.yml"
    if not model_routing_path.exists():
        default_model_routing = (
            "personas:\n"
            "  extractor:\n"
            "    model_class: cheap\n"
            "    examples: [gemini-1.5-flash, gpt-4o-mini, local-7b]\n"
            "    tasks: [memory_build, resolve_alias, summarize_continuity, classify_beats]\n"
            "  reviewer:\n"
            "    model_class: mid\n"
            "    examples: [gpt-4o, claude-3-5-haiku]\n"
            "    tasks: [validate_review, style_scan_semantic]\n"
            "  writer:\n"
            "    model_class: strong\n"
            "    examples: [claude-3-5-sonnet, gpt-4o]\n"
            "    tasks: [draft_prose]\n\n"
            "global_budget_cap_usd: 15.00\n"
        )
        model_routing_path.write_text(default_model_routing, encoding="utf-8")
        print(f"Created: {model_routing_path}")

    # Create chapters structure stub
    chapters_dir = book_folder / "chapters"
    chapters_dir.mkdir(exist_ok=True)

    # 3. Generate Agent Configurations if requested
    agent_list = []
    if hasattr(args, "agents") and args.agents:
        agent_list = [a.strip().lower() for a in args.agents.split(",") if a.strip()]
        for agent in agent_list:
            if agent == "claude":
                Path("CLAUDE.md").write_text(
                    "# Claude Code Instructions\n\nImport: AGENTS.md\n\nPlease read and follow the instructions in [AGENTS.md](AGENTS.md) at the root of this project.\n\nNote: As a Claude Code agent, you have direct CLI access. Always use the `bf` CLI command for checks and operations rather than trying to parse rulebooks or run-loops manually.\n",
                    encoding="utf-8"
                )
                print("Created: CLAUDE.md")
            elif agent == "cursor":
                Path(".cursorrules").write_text(
                    "# Cursor Instructions\n\nImport: AGENTS.md\n\nPlease read and follow the instructions in [AGENTS.md](AGENTS.md) at the root of this project.\n\nNote: Cursor should use its built-in code search and refer to `AGENTS.md` before starting to write or edit any Western manuscript draft or rulebook files.\n",
                    encoding="utf-8"
                )
                print("Created: .cursorrules")
            elif agent == "copilot":
                Path("copilot-instructions.md").write_text(
                    "# GitHub Copilot Instructions\n\nImport: AGENTS.md\n\nPlease read and follow the instructions in [AGENTS.md](AGENTS.md) at the root of this project.\n\nNote: Avoid modern or clinical language in all copilot suggestions. Refer to the style lock in `AGENTS.md`.\n",
                    encoding="utf-8"
                )
                print("Created: copilot-instructions.md")
            elif agent == "gemini":
                Path("GEMINI.md").write_text(
                    "# Gemini Agent Instructions\n\nImport: AGENTS.md\n\nPlease read and follow the instructions in [AGENTS.md](AGENTS.md) at the root of this project.\n\nNote: Gemini agents should utilize the unified `bf` command line utility to validate, loop, memory-manage, and compile manuscripts instead of invoking deprecated python helper scripts directly.\n",
                    encoding="utf-8"
                )
                print("Created: GEMINI.md")
            elif agent == "opencode":
                opencode_yml = (
                    "# OpenCode Configuration\n"
                    "model_routing:\n"
                    "  small_model:\n"
                    "    persona: extractor\n"
                    "    tasks:\n"
                    "      - memory_build\n"
                    "      - resolve_alias\n"
                    "      - summarize_continuity\n"
                    "      - classify_beats\n"
                    "  large_model:\n"
                    "    persona: writer\n"
                    "    tasks:\n"
                    "      - draft_prose\n"
                    "  reviewer_model:\n"
                    "    persona: reviewer\n"
                    "    tasks:\n"
                    "      - validate_review\n"
                    "      - style_scan_semantic\n"
                )
                Path(".opencode.yml").write_text(opencode_yml, encoding="utf-8")
                print("Created: .opencode.yml")
            elif agent == "codex":
                Path("CODEX.md").write_text(
                    "# Codex Instructions\n\nImport: AGENTS.md\n\nPlease read and follow the instructions in [AGENTS.md](AGENTS.md) at the root of this project.\n\nNote: Codex should read rulebook constraints and ensure no trial scenes, water/mineral rights, or syndicate-style conflicts are created.\n",
                    encoding="utf-8"
                )
                print("Created: CODEX.md")
            elif agent == "zed":
                Path("ZED.md").write_text(
                    "# Zed Instructions\n\nImport: AGENTS.md\n\nPlease read and follow the instructions in [AGENTS.md](AGENTS.md) at the root of this project.\n\nNote: Zed assistant should adhere to the Western manuscript style-lock rules specified in `AGENTS.md`.\n",
                    encoding="utf-8"
                )
                print("Created: ZED.md")

    # 4. Git Integration if requested
    if hasattr(args, "git") and args.git:
        import subprocess
        try:
            subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            files_to_add = [str(book_folder)]
            agent_files = {
                "claude": "CLAUDE.md",
                "cursor": ".cursorrules",
                "copilot": "copilot-instructions.md",
                "gemini": "GEMINI.md",
                "opencode": ".opencode.yml",
                "codex": "CODEX.md",
                "zed": "ZED.md"
            }
            for a in agent_list:
                if a in agent_files and Path(agent_files[a]).exists():
                    files_to_add.append(agent_files[a])
            subprocess.run(["git", "add"] + files_to_add, check=True)
            print("Initialized Git repository and staged assets.")
        except (subprocess.SubprocessError, OSError) as e:
            print(f"Warning: Git initialization failed: {e}", file=sys.stderr)

    print(f"\nSuccessfully initialized book pipeline in: '{book_folder}'")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    if not getattr(args, "book_folder", None):
        print("Error: status requires a book name or folder.", file=sys.stderr)
        print("Usage: bf status <book-name>")
        books = _available_book_names()
        if books:
            print("\nAvailable books:")
            for book in books:
                print(f"  - {book}")
        else:
            print("\nNo books found in books/.")
        return 2

    book_folder = _normalize_books_folder_arg(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    child_books = _child_book_folders(book_folder)
    if child_books and not _has_book_marker(book_folder):
        print(f"Available books in {book_folder.name}:")
        for child in child_books:
            try:
                display_path = child.relative_to(BOOKS_ROOT)
            except ValueError:
                display_path = child
            print(f"  - {display_path}")
        print(f"\nRun 'bf status <book-name>/<book-folder>' for a specific book.")
        return 0

    print(f"=== BookForge Status for {book_folder.name} ===")
    from bookforge.core.headroom import HAS_OFFICIAL_HEADROOM
    headroom_status = "ACTIVE (ML-based)" if HAS_OFFICIAL_HEADROOM else "LOCAL FALLBACK (Deterministic)"
    print(f"Context Compression (Headroom): {headroom_status}\n")

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
                print(f"  [{issue.severity.name}] {issue.message}")
        else:
            print("  [PASS] Chapter rhythm variance is healthy.")
    except (OSError, UnicodeDecodeError, ZeroDivisionError, ValueError, KeyError, AttributeError) as e:
        print(f"\nChapter Rhythm: [WARN] Could not analyze rhythm ({e})")

    print(f"\nRun 'bf run-loop {book_folder}' to see the next workflow action.")
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

    output_path = (
        Path(args.output)
        if args.output
        else compiler_module.default_output_path(book_folder, args.formatted_doc)
    )

    try:
        if args.formatted_doc:
            draft_count, word_count = compiler_module.format_manuscript_docx(
                book_folder=book_folder,
                output_path=output_path,
                include_title=not args.no_title,
            )
        else:
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
    print(f"- **Format:** {'docx' if args.formatted_doc else 'compiled'}")
    print(f"- **Draft Files Compiled:** {draft_count}")
    print(f"- **Compiled Words:** {word_count}")
    return 0


def cmd_pacing(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    reference_analysis = Path(args.reference_analysis) if args.reference_analysis else None
    try:
        markdown = pacing_module.build_plan(book_folder, reference_analysis)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    output_path = book_folder / "chapter-pacing-plan.md"
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


def cmd_packet(args: argparse.Namespace) -> int:
    book_folder = _shift_scene_args(args)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    scene = getattr(args, "scene", None)
    if scene:
        from bookforge.core.scene import parse_scene_id
        from bookforge.core.packet.builder import build_scene_packet
        from bookforge.core.packet.helpers import scene_folder
        
        ch, sc = parse_scene_id(scene)
        chapter = args.chapter or ch
        if not chapter:
            print("Error: --chapter must be specified or included in --scene value (e.g. chapter-08/scene-02).", file=sys.stderr)
            return 2
            
        try:
            markdown = build_scene_packet(book_folder, chapter, sc)
        except Exception as error:
            print(f"Error building scene packet: {error}", file=sys.stderr)
            return 2
            
        folder = scene_folder(book_folder, chapter, sc)
        folder.mkdir(parents=True, exist_ok=True)
        out_p = folder / "generation-packet.md"
        out_p.write_text(markdown, encoding="utf-8")
        print(f"Wrote scene generation-packet.md to {out_p}")
        
        # Increment generation attempts in queue and update status
        try:
            from bookforge.core.queue import update_queue_scene
            update_queue_scene(book_folder, f"{chapter}/{sc}", status="generation_packet_ready", inc_generation=True)
        except Exception:
            pass
            
        return 0

    if not args.chapter:
        print("Error: --chapter is required (e.g. chapter-01).", file=sys.stderr)
        return 2

    try:
        task = getattr(args, "task", "all")
        markdown = packet_module.render_packet(book_folder, args.chapter, task)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    output_folder = packet_module.chapter_folder(book_folder, args.chapter)
    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / "context-packet.md"
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


def cmd_analytics(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    data = analytics_module.load_analytics(book_folder)
    file_analytics = analytics_module.get_project_file_analytics(book_folder)

    print(f"# BookForge Analytics: {book_folder.name}")
    print("")
    print("## Cumulative API Token Log")
    print(f"- **Total Orchestration Runs:** {data['total_runs']}")
    print(f"- **Last Model Used:** `{data['last_model_used']}`")
    print(f"- **Total Cumulative Tokens:** {data['total_input_tokens'] + data['total_output_tokens']:,} ({data['total_input_tokens']:,} In / {data['total_output_tokens']:,} Out)")
    print("")
    print("## Project Files Metrics")
    print("| File | Lines | Words | Characters | Est. Tokens |")
    print("| --- | --- | --- | --- | --- |")
    
    for name in ["outline", "rulebook", "mood_lock", "chapter_summaries", "research_pack"]:
        if name in file_analytics:
            f = file_analytics[name]
            m = f["metrics"]
            print(f"| {f['filename']} | {m['lines']} | {m['words']} | {m['chars']} | {m['tokens']} |")
            
    for chap in file_analytics.get("chapters", []):
        for f_key in ["scene_breakdown", "draft", "continuity_out"]:
            if f_key in chap["files"]:
                f = chap["files"][f_key]
                m = f["metrics"]
                print(f"| {chap['slug']}/{f['filename']} | {m['lines']} | {m['words']} | {m['chars']} | {m['tokens']} |")
                
    return 0


def cmd_log_run(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    analytics_module.log_run(
        book_folder=book_folder,
        model=args.model,
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        action=args.action
    )
    print(f"Successfully logged run metrics for model '{args.model}' under '{args.action}'.")
    return 0


def cmd_tui(args: argparse.Namespace) -> int:
    from bookforge.tui import BookForgeTUI
    tui = BookForgeTUI()
    tui.run()
    return 0


def cmd_init_action(args: argparse.Namespace) -> int:
    import re
    chapter_folder = Path(args.chapter_folder)
    scene_id = args.scene
    
    # Extract scene_id clean name
    match = re.search(r"(?i)scene[-_ ]*(\d+|\w+)", scene_id)
    if match:
        clean_scene_id = f"scene-{match.group(1).lower()}"
    else:
        clean_scene_id = "scene-" + re.sub(r"[^a-z0-9]+", "-", scene_id.lower()).strip("-")
    
    clean_scene_id = clean_scene_id.replace("-combat", "")

    plan_path = action_module.init_action_plan(chapter_folder, clean_scene_id)
    print(f"Initialized template action plan for scene '{scene_id}' in: {plan_path}")
    return 0


def cmd_repair(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    return repair_module.run_repair_wizard(book_folder, args.chapter_slug)


def cmd_resolve_unknowns(args: argparse.Namespace) -> int:
    from bookforge.core import unknowns as unknowns_module
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    return unknowns_module.run_unknowns_wizard(book_folder)


def cmd_add_relation(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    rel = relationship_module.add_relationship(
        book_folder=book_folder,
        subject=args.subject,
        relation=args.relation,
        obj=args.object,
        source_artifact=args.source
    )
    print(f"Added relationship: {rel['subject']} {rel['relation']} {rel['object']} (source: {rel['source_artifact']})")
    return 0


def cmd_check_persona(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    persona_name = args.persona
    model = args.model
    action = args.action
    projected_tokens = args.projected_tokens

    is_allowed, reason = persona_module.check_persona_capabilities(
        book_folder=book_folder,
        persona_name=persona_name,
        model=model,
        action=action,
        projected_input_tokens=projected_tokens
    )

    if not is_allowed:
        print(f"REJECTED: {reason}")
        return 1

    print(f"AUTHORIZED: {reason}")
    return 0


def cmd_nlm(args: argparse.Namespace) -> int:
    from bookforge.core import notebooklm
    
    if args.nlm_command == "list":
        if not notebooklm.is_nlm_available():
            print("Error: nlm CLI tool not found in PATH.", file=sys.stderr)
            return 1
        
        auth = notebooklm.get_auth_status()
        if not auth["authenticated"]:
            print(f"Warning: {auth['error']}", file=sys.stderr)
        else:
            print(f"Authenticated as: {auth['email']}")
            
        print("\nRetrieving notebooks...")
        nbs = notebooklm.list_notebooks()
        if not nbs:
            print("No notebooks found or failed to query.")
            return 0
            
        print(f"{'Notebook Title':<40} | {'Notebook ID':<36} | Sources")
        print("-" * 88)
        for nb in nbs:
            print(f"{nb['title'][:40]:<40} | {nb['id']:<36} | {nb['sources']}")
        return 0

    # For other commands, we need book_folder
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: Book folder not found: {book_folder}", file=sys.stderr)
        return 2

    if args.nlm_command == "status":
        auth = notebooklm.get_auth_status()
        print(f"Authenticated: {'Yes (' + auth['email'] + ')' if auth['authenticated'] else 'No (' + str(auth['error']) + ')'}")
        
        nb = notebooklm.get_associated_notebook(book_folder)
        if nb:
            print(f"Linked Notebook: {nb['title']} (ID: {nb['id']})")
        else:
            print("Linked Notebook: None. Run 'bf nlm link <notebook_id>' to link.")
        return 0

    elif args.nlm_command == "link":
        nbs = notebooklm.list_notebooks()
        title = args.title
        if not title:
            for n in nbs:
                if n["id"] == args.notebook_id:
                    title = n["title"]
                    break
            if not title:
                series_info = series_module.get_series_info(book_folder)
                if series_info:
                    title = series_info["name"].lower().replace(" ", "-")
                else:
                    title = book_folder.name
                
        notebooklm.set_associated_notebook(book_folder, args.notebook_id, title)
        print(f"Successfully linked notebook '{title}' (ID: {args.notebook_id}) to '{book_folder}'.")
        return 0

    elif args.nlm_command == "query":
        nb = notebooklm.get_associated_notebook(book_folder)
        if not nb:
            print(f"Error: No notebook linked to '{book_folder}'. Run 'bf nlm link <notebook_id>' first.", file=sys.stderr)
            return 1
        print(f"Querying linked notebook '{nb['title']}'...")
        answer = notebooklm.query_notebook(nb["id"], args.query_text)
        print(f"\nResponse:\n{answer}")
        return 0

    elif args.nlm_command == "sync-research":
        nb = notebooklm.get_associated_notebook(book_folder)
        if not nb:
            print(f"Error: No notebook linked to '{book_folder}'. Run 'bf nlm link <notebook_id>' first.", file=sys.stderr)
            return 1
        pack_path = research_module.get_research_pack_path(book_folder)
        print(f"Syncing research from '{nb['title']}' to '{pack_path}'...")
        success = notebooklm.sync_research_to_pack(book_folder, nb["id"])
        if success:
            print("Successfully synced research pack.")
            return 0
        else:
            print("Failed to sync research pack.", file=sys.stderr)
            return 1

    elif args.nlm_command == "sync-sources":
        nb = notebooklm.get_associated_notebook(book_folder)
        if not nb:
            print(f"Error: No notebook linked to '{book_folder}'. Run 'bf nlm link <notebook_id>' first.", file=sys.stderr)
            return 1
        print(f"Uploading local files from '{book_folder}' to linked notebook '{nb['title']}'...")
        uploaded = notebooklm.upload_local_sources(book_folder, nb["id"])
        if uploaded:
            print(f"Successfully uploaded {len(uploaded)} sources:")
            for f in uploaded:
                print(f"  - {f}")
        else:
            print("No sources uploaded or upload failed.")
        return 0

    elif args.nlm_command == "generate-outline":
        print(f"Generating research-grounded outline for '{book_folder}'...")
        success, msg = notebooklm.generate_research_outline(book_folder)
        if success:
            print(msg)
            return 0
        else:
            print(msg, file=sys.stderr)
            return 1

    return 0


def cmd_canon(args: argparse.Namespace) -> int:
    from bookforge.core import canon
    book_folder = Path(args.book_folder)
    if args.canon_command == "build":
        print(f"Folding canon for '{book_folder}'...")
        canon.fold_canon(book_folder)
        print("Canon successfully folded and written to canon/state/snapshot.yml")
        return 0
    elif args.canon_command == "validate":
        print(f"Validating canon for '{book_folder}'...")
        issues = canon.validate_canon(book_folder)
        has_hard = any(i.is_hard for i in issues)
        for i in issues:
            lbl = "FAIL" if i.is_hard else "WARN"
            print(f"  [{lbl}] {i.message}")
        if has_hard:
            print("Validation failed with hard errors.")
            return 1
        print("Canon is valid.")
        return 0
    return 1


def cmd_validate(args: argparse.Namespace) -> int:
    from bookforge.core import validator as context_validator
    from bookforge.core import canon
    from bookforge.core.issue import Severity
    
    book_folder = _shift_scene_args(args)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    # If --scene is specified, run scene-level validation instead of full chapter/book validation
    scene = getattr(args, "scene", None)
    if scene:
        from bookforge.core.scene import parse_scene_id, load_scene_manifest, manifest_path
        from bookforge.core.packet.helpers import scene_folder
        from bookforge.core.validators.orchestration import validate_scene
        from bookforge.core.queue import update_queue_scene
        
        ch, sc = parse_scene_id(scene)
        chapter_slug = args.chapter or ch
        if not chapter_slug:
            print("Error: --chapter must be specified or included in --scene value (e.g. chapter-08/scene-02).", file=sys.stderr)
            return 2
            
        s_folder = scene_folder(book_folder, chapter_slug, sc)
        m_path = manifest_path(s_folder.parent.parent, sc)
        if not m_path.exists():
            m_path = s_folder / "manifest.yml"
            
        if not m_path.exists():
            print(f"Error: scene manifest not found for {scene}", file=sys.stderr)
            return 2
            
        manifest = load_scene_manifest(m_path, book_folder)
        issues = validate_scene(manifest)
        
        failures = [i.message for i in issues if i.severity == Severity.HARD]
        warnings = [i.message for i in issues if i.severity == Severity.SOFT]
        passes = [] if failures or warnings else ["Scene draft is clean and meets all rules."]
        
        print(f"=== Scene Validation Report: {chapter_slug}/{sc} ===")
        if passes:
            for p in passes:
                print(f"[PASS] {p}")
        if warnings:
            for w in warnings:
                print(f"[WARN] {w}")
        if failures:
            for f in failures:
                print(f"[FAIL] {f}")
                
        # Write validation result to file
        val_data = {
            "status": "failed" if failures else "clean",
            "errors": failures + warnings,
            "failed_rules": failures
        }
        import json
        (s_folder / "validation.json").write_text(json.dumps(val_data, indent=2), encoding="utf-8")
        
        # Update queue
        new_status = "validation_failed" if failures else "validation_passed"
        try:
            update_queue_scene(book_folder, f"{chapter_slug}/{sc}", status=new_status)
        except Exception:
            pass
            
        return 1 if failures else 0

    chapters = context_validator.discover_chapters(book_folder)
    if args.chapter:
        chapters = [chapter for chapter in chapters if chapter.slug == args.chapter]
        if not chapters:
            print(f"Error: chapter not found: {args.chapter}", file=sys.stderr)
            return 2

    if args.review_prompt:
        if len(chapters) != 1:
            print("Error: --review-prompt requires exactly one chapter via --chapter.", file=sys.stderr)
            return 2
        try:
            print(context_validator.build_ai_prompt(book_folder, chapters[0]))
        except RuntimeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        return 0

    book_issues = list(context_validator.validate_required_book_file_issues(book_folder))
    canon_issues = canon.validate_canon(book_folder)
    book_issues.extend(canon_issues)

    book_passes = [i.message for i in book_issues if i.severity == Severity.INFO]
    book_failures = [i.message for i in book_issues if i.severity == Severity.HARD]
    book_warnings = [i.message for i in book_issues if i.severity == Severity.SOFT]

    phase_sections = context_validator.parse_phase_chapters(book_folder)
    reports = [context_validator.validate_chapter(chapter, phase_sections) for chapter in chapters]

    print(context_validator.render_report(book_folder, book_passes, book_failures, book_warnings, reports))
    return 1 if context_validator.overall_status(book_failures, reports) == "FAIL" else 0


def cmd_apply(args: argparse.Namespace) -> int:
    from bookforge.core import canon
    from bookforge.core import validator as context_validator
    from bookforge.core.issue import Severity
    import shutil
    book_folder = Path(args.book_folder)

    if args.apply_command == "change":
        chapter_id = args.chapter_id

        # Pre-validation
        print(f"Pre-validating changes for '{chapter_id}'...")
        chapters = context_validator.discover_chapters(book_folder)
        target_ch = [c for c in chapters if c.slug == chapter_id]

        if not target_ch:
            print(f"Error: Chapter '{chapter_id}' not found in changes/ or chapters/.", file=sys.stderr)
            return 1

        ch_files = target_ch[0]

        book_issues = list(context_validator.validate_required_book_file_issues(book_folder))
        canon_issues = canon.validate_canon(book_folder)
        book_issues.extend(canon_issues)

        book_failures = [i.message for i in book_issues if i.severity == Severity.HARD]
        phase_sections = context_validator.parse_phase_chapters(book_folder)
        reports = [context_validator.validate_chapter(ch_files, phase_sections)]

        if context_validator.overall_status(book_failures, reports) == "FAIL":
            print("Error: Validation failed. Cannot apply change.", file=sys.stderr)
            # Print failure details to help user/agent diagnose
            for msg in book_failures:
                print(f"  [BOOK FAILURE] {msg}", file=sys.stderr)
            for r in reports:
                for msg in r.failures:
                    print(f"  [CHAPTER FAILURE] {msg}", file=sys.stderr)
            return 1

        # Check for continuity-out.md
        continuity_path = ch_files.folder / "continuity-out.md"
        if not continuity_path.exists():
            print(f"Error: Missing continuity-out.md for {chapter_id} in {ch_files.folder}.", file=sys.stderr)
            return 1

        # 1. Append Event & Re-fold Canon
        change_data = canon.parse_continuity_out_to_event(continuity_path)
        canon.apply_chapter_event(book_folder, chapter_id, change_data)
        print(f"Applied event for {chapter_id} and re-folded snapshot.")

        # 2. Compile Draft & Archive Change
        if "changes" in ch_files.folder.parts:
            dest_dir = book_folder / "chapters" / chapter_id
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            dest_draft_name = "epilogue.md" if chapter_id == "epilogue" else f"{chapter_id}.md"
            
            # Copy active authoring files to canonical names
            if ch_files.draft.exists():
                shutil.copy2(ch_files.draft, dest_dir / dest_draft_name)
            if ch_files.scene_breakdown.exists():
                shutil.copy2(ch_files.scene_breakdown, dest_dir / "scene-breakdown.md")
            if ch_files.drafting_plan.exists():
                shutil.copy2(ch_files.drafting_plan, dest_dir / "drafting-plan.md")
            shutil.copy2(continuity_path, dest_dir / "continuity-out.md")
            
            print(f"Compiled draft files into {dest_dir}")

            # Archive staging folder
            archive_dir = book_folder / ".bookforge" / "archive" / "changes" / chapter_id
            if archive_dir.exists():
                shutil.rmtree(archive_dir)
            archive_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(ch_files.folder), str(archive_dir))
            print(f"Archived staging folder to {archive_dir}")

        return 0
    return 1


def cmd_migrate(args: argparse.Namespace) -> int:
    from bookforge.core import canon
    book_folder = Path(args.book_folder)
    print(f"Migrating '{book_folder}' legacy assets to v2 event-sourced canon...")
    canon.migrate_legacy_book(book_folder)
    print("Migration complete. Event-sourced canon is active.")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    from bookforge.core import checkpoint as checkpoint_core
    book_folder = Path(args.book_folder)

    if args.checkpoint_command == "save":
        print(f"Saving checkpoint '{args.name}' for '{book_folder}'...")
        checkpoint_core.save_checkpoint(book_folder, args.name)
        print(f"Checkpoint '{args.name}' saved successfully.")
        return 0

    elif args.checkpoint_command == "load":
        print(f"Loading checkpoint '{args.name}' for '{book_folder}'...")
        try:
            checkpoint_core.load_checkpoint(book_folder, args.name)
            print(f"Checkpoint '{args.name}' loaded successfully.")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif args.checkpoint_command == "restore":
        print(f"Restoring checkpoint '{args.name}' for '{book_folder}'...")
        try:
            checkpoint_core.restore_checkpoint(book_folder, args.name)
            print(f"Checkpoint '{args.name}' restored successfully.")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif args.checkpoint_command == "diff":
        try:
            diff_text = checkpoint_core.diff_checkpoint(book_folder, args.name)
            if diff_text.strip():
                print(diff_text)
            else:
                print("No differences found.")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 1


def _shift_scene_args(args: argparse.Namespace) -> Path:
    """Detects if chapter slug is passed in book_folder and shifts parameters.
    
    Returns the resolved book_folder Path.
    """
    import re
    raw_folder = getattr(args, "book_folder", None)
    book_folder = _normalize_books_folder_arg(raw_folder or "books/book-example")
    
    if raw_folder and (raw_folder.startswith("chapter-") or raw_folder.startswith("ch-") or re.match(r"^ch\d+", raw_folder)):
        if hasattr(args, "chapter") and not args.chapter:
            args.chapter = raw_folder
        book_folder = _normalize_books_folder_arg("books/book-example")
        
    return book_folder


def cmd_scene(args: argparse.Namespace) -> int:
    """Handles scene subcommands (init, packet, report)."""
    subcommand = getattr(args, "scene_command", None)
    if subcommand == "init":
        book_folder = _shift_scene_args(args)
        if not book_folder.exists():
            print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
            return 2
            
        scene_id = getattr(args, "scene_id", None) or getattr(args, "scene", None)
        if not scene_id:
            print("Error: --scene-id is required.", file=sys.stderr)
            return 2

        from bookforge.core.scene import parse_scene_id, init_scene_manifest
        ch, sc = parse_scene_id(scene_id)
        chapter = args.chapter or ch
        if not chapter:
            print("Error: --chapter must be specified or included in scene identifier (e.g. ch08_sc02).", file=sys.stderr)
            return 2

        target_words = getattr(args, "target_words", 3500)
        m_path = init_scene_manifest(book_folder, chapter, sc, target_words)
        print(f"Initialized scene manifest at: {m_path}")
        
        # Update/sync the queue status
        try:
            from bookforge.core.queue import update_queue_scene
            update_queue_scene(book_folder, f"{chapter}/{sc}", status="ready_for_generation", target_words=target_words)
        except Exception:
            pass
            
        return 0

    elif subcommand == "packet":
        book_folder = _shift_scene_args(args)
        if not book_folder.exists():
            print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
            return 2
            
        scene_id = getattr(args, "scene_id", None) or getattr(args, "scene", None)
        if not scene_id:
            print("Error: --scene-id is required.", file=sys.stderr)
            return 2

        from bookforge.core.scene import parse_scene_id
        ch, sc = parse_scene_id(scene_id)
        chapter = args.chapter or ch
        if not chapter:
            print("Error: --chapter must be specified or included in scene identifier (e.g. ch08_sc02).", file=sys.stderr)
            return 2

        from bookforge.core.packet.builder import build_scene_packet
        try:
            markdown = build_scene_packet(book_folder, chapter, sc)
        except Exception as error:
            print(f"Error building scene packet: {error}", file=sys.stderr)
            return 2

        from bookforge.core.packet.helpers import scene_folder
        folder = scene_folder(book_folder, chapter, sc)
        folder.mkdir(parents=True, exist_ok=True)
        out_p = folder / "generation-packet.md"
        out_p.write_text(markdown, encoding="utf-8")
        print(f"Wrote scene generation-packet.md to {out_p}")
        
        # Increment generation attempts in queue and update status
        try:
            from bookforge.core.queue import update_queue_scene
            update_queue_scene(book_folder, f"{chapter}/{sc}", status="generation_packet_ready", inc_generation=True)
        except Exception:
            pass
            
        return 0

    elif subcommand == "report":
        import re
        raw_folder = args.book_folder
        chapter = args.chapter
        scene_id = args.scene_id
        
        # Shift logic specifically for report positional arguments
        if raw_folder and (raw_folder.startswith("chapter-") or raw_folder.startswith("ch-") or re.match(r"^ch\d+", raw_folder)):
            scene_id = chapter
            chapter = raw_folder
            book_folder = _normalize_books_folder_arg("books/book-example")
        else:
            book_folder = _normalize_books_folder_arg(raw_folder or "books/book-example")
            
        if not book_folder.exists():
            print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
            return 2
            
        if not chapter or not scene_id:
            print("Error: Both chapter and scene-id are required.", file=sys.stderr)
            return 2
            
        from bookforge.core.scene import parse_scene_id, load_scene_manifest
        from bookforge.core.packet.helpers import scene_folder, scene_draft_path
        from bookforge.core.queue import load_queue
        
        ch, sc_id = parse_scene_id(scene_id)
        ch_slug = chapter or ch
        
        s_folder = scene_folder(book_folder, ch_slug, sc_id)
        m_path = s_folder / "manifest.yml"
        if not m_path.exists():
            m_path = s_folder.parent.parent / "scenes" / sc_id / "manifest.yml"
            
        if not m_path.exists():
            print(f"Error: Scene manifest not found for {ch_slug}/{sc_id}", file=sys.stderr)
            return 2
            
        manifest = load_scene_manifest(m_path, book_folder)
        
        # Draft word count
        draft_p = scene_draft_path(s_folder, sc_id)
        draft_words = 0
        if draft_p.exists():
            try:
                draft_words = len(draft_p.read_text(encoding="utf-8").split())
            except Exception:
                pass
                
        # Packet token estimation
        packet_p = s_folder / "generation-packet.md"
        packet_tokens = 0
        if packet_p.exists():
            try:
                from bookforge.core.analytics import estimate_tokens
                packet_tokens = estimate_tokens(packet_p.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        # Patch token estimation
        patch_packet_p = s_folder / "patch-packet.md"
        patch_tokens = 0
        if patch_packet_p.exists():
            try:
                from bookforge.core.analytics import estimate_tokens
                patch_tokens = estimate_tokens(patch_packet_p.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        # Validation status
        val_json = s_folder / "validation.json"
        val_status = "unknown"
        if val_json.exists():
            try:
                import json
                val_data = json.loads(val_json.read_text(encoding="utf-8"))
                val_status = "passed" if val_data.get("status") == "clean" else "failed"
            except Exception:
                pass
        elif manifest.status == "clean":
            val_status = "passed"
            
        # Attempts and provider from queue
        q_data = load_queue(book_folder)
        attempts_patch = 0
        provider = "manual-web"
        for s in q_data.get("scenes", []):
            if s["scene_key"] == f"{ch_slug}/{sc_id}":
                attempts_patch = s["attempts"].get("patch", 0)
                provider = s.get("provider", "manual-web")
                if val_status == "unknown":
                    if s["status"] in ("clean", "validation_passed"):
                        val_status = "passed"
                    elif s["status"] in ("validation_failed", "ready_for_patch", "patch_packet_ready"):
                        val_status = "failed"
                break
                
        # Guard warnings
        guard_log_p = s_folder / "guard-log.jsonl"
        guard_warnings = 0
        if guard_log_p.exists():
            try:
                with open(guard_log_p, "r", encoding="utf-8") as f:
                    for line in f:
                        if "warning" in line.lower() or "violation" in line.lower() or "fail" in line.lower():
                            guard_warnings += 1
            except Exception:
                pass
                
        # Output formatting
        print(f"Scene: {ch_slug}/{sc_id}")
        print(f"Target words: {manifest.target_words}")
        print(f"Draft words: {draft_words}")
        print(f"Packet tokens: {packet_tokens}")
        print(f"Patch tokens: {patch_tokens}")
        print(f"Validation: {val_status}")
        print(f"Patch attempts: {attempts_patch}")
        print(f"Guard warnings: {guard_warnings}")
        print(f"Provider lane: {provider}")
        print(f"Status: {manifest.status}")
        return 0

    else:
        print("Error: Invalid or missing scene subcommand. Use init, packet, or report.", file=sys.stderr)
        return 2


def cmd_patch(args: argparse.Namespace) -> int:
    """Handles patch subcommands (build, splice, apply)."""
    subcommand = getattr(args, "patch_command", None)
    if subcommand is None:
        subcommand = "build"
        args.scene_id = getattr(args, "scene", None) or getattr(args, "scene_id", None)

    if subcommand == "build":
        book_folder = _shift_scene_args(args)
        if not book_folder.exists():
            print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
            return 2
            
        scene_id = getattr(args, "scene_id", None) or getattr(args, "scene", None)
        if not scene_id:
            print("Error: --scene-id is required.", file=sys.stderr)
            return 2

        from bookforge.core.scene import parse_scene_id, load_scene_manifest, manifest_path
        ch, sc = parse_scene_id(scene_id)
        chapter = args.chapter or ch
        if not chapter:
            print("Error: --chapter must be specified or included in scene identifier (e.g. ch08_sc02).", file=sys.stderr)
            return 2

        from bookforge.core.packet.helpers import scene_folder
        folder = scene_folder(book_folder, chapter, sc)
        m_path = manifest_path(folder.parent.parent, sc)
        if not m_path.exists():
            m_path = folder / "manifest.yml"

        if not m_path.exists():
            print(f"Error: scene manifest not found for {scene_id}", file=sys.stderr)
            return 2

        manifest = load_scene_manifest(m_path, book_folder)
        failed_rules = args.failed_rules or []
        if not failed_rules:
            val_json_path = folder / "validation.json"
            if val_json_path.exists():
                try:
                    import json
                    val_data = json.loads(val_json_path.read_text(encoding="utf-8"))
                    failed_rules = val_data.get("failed_rules", []) or val_data.get("errors", [])
                except Exception:
                    pass
            if not failed_rules:
                failed_rules = ["Generic style validation failure. Check style guide."]

        from bookforge.core.patch import build_patch_packet
        patch_content = build_patch_packet(manifest, failed_rules)
        out_p = folder / "patch-packet.md"
        out_p.write_text(patch_content, encoding="utf-8")
        print(f"Wrote patch-packet.md to {out_p}")
        
        # Update queue status and increment patch attempts
        try:
            from bookforge.core.queue import update_queue_scene
            update_queue_scene(book_folder, f"{chapter}/{sc}", status="patch_packet_ready", inc_patch=True)
        except Exception:
            pass
            
        return 0

    elif subcommand in ("splice", "apply"):
        book_folder = _shift_scene_args(args)
        if not book_folder.exists():
            print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
            return 2
            
        scene_id = getattr(args, "scene_id", None) or getattr(args, "scene", None)
        if not scene_id:
            print("Error: --scene-id is required.", file=sys.stderr)
            return 2

        from bookforge.core.scene import parse_scene_id, load_scene_manifest
        from bookforge.core.packet.helpers import scene_folder
        ch, sc = parse_scene_id(scene_id)
        chapter = args.chapter or ch
        if not chapter:
            print("Error: --chapter must be specified or included in scene identifier (e.g. ch08_sc02).", file=sys.stderr)
            return 2

        folder = scene_folder(book_folder, chapter, sc)
        draft_p = folder / "draft.md"
        repl_p = folder / "replacement.md"

        from_file = getattr(args, "from_file", None)
        if from_file:
            from_file_path = Path(from_file)
            if from_file_path.exists():
                folder.mkdir(parents=True, exist_ok=True)
                shutil.copy2(from_file_path, repl_p)
                print(f"Copied replacement from {from_file} to {repl_p}")
            else:
                print(f"Error: source file from --from-file does not exist: {from_file_path}", file=sys.stderr)
                return 2

        if not draft_p.exists():
            print(f"Error: scene draft.md does not exist at {draft_p}", file=sys.stderr)
            return 2
        if not repl_p.exists():
            print(f"Error: scene replacement.md does not exist at {repl_p}", file=sys.stderr)
            return 2

        original = draft_p.read_text(encoding="utf-8")
        replacement = repl_p.read_text(encoding="utf-8")

        from bookforge.core.patch import splice_prose, validate_merged_prose
        success, merged = splice_prose(original, replacement)
        if not success:
            print(f"Splicing failed: {merged}", file=sys.stderr)
            return 1

        m_path = folder / "manifest.yml"
        if not m_path.exists():
            m_path = folder.parent.parent / "scenes" / sc / "manifest.yml"
        if m_path.exists():
            manifest = load_scene_manifest(m_path, book_folder)
            target_words = manifest.target_words
        else:
            target_words = 3500

        errors = validate_merged_prose(merged, target_words)
        if errors:
            print("Merged prose failed validation checks:", file=sys.stderr)
            for err in errors:
                print(f"- {err}", file=sys.stderr)
            val_data = {"status": "failed", "errors": errors}
            import json
            (folder / "validation.json").write_text(json.dumps(val_data, indent=2), encoding="utf-8")
            
            # Update queue status
            try:
                from bookforge.core.queue import update_queue_scene
                update_queue_scene(book_folder, f"{chapter}/{sc}", status="validation_failed")
            except Exception:
                pass
                
            return 1

        draft_p.write_text(merged, encoding="utf-8")
        val_data = {"status": "clean", "errors": []}
        import json
        (folder / "validation.json").write_text(json.dumps(val_data, indent=2), encoding="utf-8")

        if m_path.exists():
            manifest.status = "clean"
            from bookforge.core.scene import save_scene_manifest
            save_scene_manifest(manifest, m_path)

        # Update queue status
        try:
            from bookforge.core.queue import update_queue_scene
            update_queue_scene(book_folder, f"{chapter}/{sc}", status="validation_passed")
        except Exception:
            pass

        print(f"Successfully spliced patch and updated draft.md at {draft_p}")
        return 0
    else:
        print("Error: Invalid or missing patch subcommand. Use build, splice, or apply.", file=sys.stderr)
        return 2


def cmd_queue(args: argparse.Namespace) -> int:
    """Handles queue subcommands (build, show, update)."""
    subcommand = getattr(args, "queue_command", None)
    if not subcommand:
        print("Error: Invalid or missing queue subcommand. Use build, show, or update.", file=sys.stderr)
        return 2

    book_folder = _normalize_books_folder_arg(args.book_folder)
    from bookforge.core import queue as queue_core

    if subcommand == "build":
        if not book_folder.exists():
            print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
            return 2
        q_path = queue_core.build_queue(book_folder)
        print(f"Queue compiled successfully and written to {q_path}")
        return 0

    elif subcommand == "show":
        if not book_folder.exists():
            print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
            return 2
        queue_data = queue_core.load_queue(book_folder)
        scenes = queue_data.get("scenes", [])
        print(f"Queue for: {queue_data.get('book', book_folder.name)}")
        print("=" * 60)
        if not scenes:
            print("No scenes in queue. Run 'bf queue build' first.")
            return 0
            
        for s in scenes:
            key = s["scene_key"]
            status = s["status"]
            provider = s["provider"]
            gen_att = s["attempts"].get("generation", 0)
            pat_att = s["attempts"].get("patch", 0)
            deps = s["dependencies"]
            
            if status in ("clean", "validation_passed"):
                prefix = "[DONE]"
            elif status in ("ready_for_patch", "patch_packet_ready", "validation_failed"):
                prefix = "[REPAIR]"
            elif status in ("ready_for_generation", "generation_packet_ready"):
                prefix = "[ACTIVE]"
            else:
                prefix = "[PENDING]"
                
            att_str = f"(attempts: gen={gen_att}, patch={pat_att})"
            dep_str = f" (depends on: {', '.join(deps)})" if deps else ""
            print(f"{prefix:<9} {key:<20} {status:<24} {provider:<12} {att_str}{dep_str}")
        return 0

    elif subcommand == "update":
        if not book_folder.exists():
            print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
            return 2
        if not args.scene_key:
            print("Error: --scene-key is required.", file=sys.stderr)
            return 2
            
        status = getattr(args, "status", None)
        provider = getattr(args, "provider", None)
        inc_gen = getattr(args, "inc_generation", False)
        inc_patch = getattr(args, "inc_patch", False)
        
        success = queue_core.update_queue_scene(
            book_folder,
            args.scene_key,
            status=status,
            provider=provider,
            inc_generation=inc_gen,
            inc_patch=inc_patch
        )
        if success:
            print(f"Successfully updated scene '{args.scene_key}' in queue.")
            return 0
        else:
            print(f"Error: scene '{args.scene_key}' not found in queue.", file=sys.stderr)
            return 1

    return 2


def cmd_memory(args: argparse.Namespace) -> int:
    from bookforge.core import memory as memory_core
    import uuid
    import yaml
    
    book_folder = Path(args.book_folder)
    backend = memory_core.get_memory_backend(book_folder)
    
    if args.memory_command == "build":
        print(f"Building memory index for '{book_folder}'...")
        backend.build(book_folder)
        stats = backend.stats()
        print(f"Memory build complete. Backend: {stats.backend_type}. Memories indexed: {stats.num_memories}")
        return 0
        
    elif args.memory_command == "retrieve":
        print(f"Searching memory for: '{args.query}'")
        chunks = backend.retrieve(args.query, limit=args.limit)
        if not chunks:
            print("No relevant memories found.")
            return 0
        for i, chunk in enumerate(chunks, 1):
            source_file = chunk.metadata.get("file", "unknown")
            print(f"[{i}] Score: {chunk.score:.4f} | Source: {source_file}")
            print(f"    {chunk.content}")
            print("-" * 60)
        return 0
        
    elif args.memory_command == "resolve":
        print(f"Resolving alias: '{args.name}'")
        resolved = backend.resolve(book_folder, args.name)
        if resolved:
            print(f"Resolved to Canonical ID: '{resolved}'")
        else:
            print("Could not resolve name.")
        return 0
        
    elif args.memory_command == "learn":
        log_path = Path(args.log_file)
        if args.log_file == "-":
            log_content = sys.stdin.read()
        elif log_path.exists():
            log_content = log_path.read_text(encoding="utf-8")
        else:
            print(f"Error: Log file not found: {args.log_file}", file=sys.stderr)
            return 1
            
        print("Analyzing validation log and proposing corrective rules...")
        rules = backend.learn(log_content)
        if not rules:
            print("No corrective rules proposed.")
            return 0
            
        # Create proposals directory
        proposals_dir = book_folder / ".bookforge" / "proposals"
        proposals_dir.mkdir(parents=True, exist_ok=True)
        
        proposal_id = str(uuid.uuid4())
        proposal_file = proposals_dir / f"{proposal_id}.yml"
        
        proposal_data = {
            "proposal_id": proposal_id,
            "rules": [
                {
                    "id": r.id,
                    "pattern": r.pattern,
                    "replacement": r.replacement,
                    "reason": r.reason,
                    "file": r.file,
                    "change": r.change
                }
                for r in rules
            ]
        }
        
        proposal_file.write_text(yaml.dump(proposal_data, sort_keys=False), encoding="utf-8")
        print(f"\nGenerated Rule Proposal: {proposal_id}")
        print(f"Saved to: {proposal_file}")
        print("\nProposed Rules:")
        for r in rules:
            print(f"  - [{r.id}] Target: {r.file}")
            print(f"    Reason: {r.reason}")
            print(f"    Change:\n{r.change}")
            print()
        return 0
        
    elif args.memory_command == "apply-learning":
        proposal_id = args.proposal_id
        print(f"Applying rule proposal '{proposal_id}'...")
        try:
            modified = memory_core.apply_proposal_rules(book_folder, proposal_id)
            print("Successfully applied rules. Modified files:")
            for f in modified:
                print(f"  - {f}")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
            
    elif args.memory_command == "serve":
        server = memory_core.MemoryMCPServer(backend)
        if args.http:
            print(f"Starting memory MCP HTTP Server on port {args.port}...")
            server.run_http(port=args.port)
        else:
            print("Starting memory MCP stdio Server...")
            server.run_stdio()
        return 0
        
    return 1




def main() -> int:
    parser = argparse.ArgumentParser(
        description="BookForge: A Production-Ready Manuscript Workflow Pipeline",
        prog="bookforge"
    )
    subparsers = parser.add_subparsers(dest="command", required=False)

    # init
    parser_init = subparsers.add_parser("init", help="Initialize a new book structure")
    parser_init.add_argument("book_folder", help="Path to book folder (e.g. books/my-book)")
    parser_init.add_argument("--carry-from", "--from", dest="carry_from", help="Optional path to completed prior book in the series")
    parser_init.add_argument("--agents", help="Comma-separated list of agents to configure (e.g. opencode,claude,cursor,copilot,gemini,codex,zed)")
    parser_init.add_argument("--git", action="store_true", help="Initialize a Git repository and stage assets")

    # status
    parser_status = subparsers.add_parser("status", help="Show pipeline diagnostics and validations")
    parser_status.add_argument("book_folder", nargs="?", help="Book name or path under books/")

    # run-loop
    parser_run = subparsers.add_parser("run-loop", help="Check loop state and print next action")
    parser_run.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_run.add_argument("--target-min", type=int, help="Target minimum words")
    parser_run.add_argument("--target-max", type=int, help="Target maximum words")
    parser_run.add_argument("--repair-attempt", help="Comma-separated repair overrides (e.g. chapter-01:3)")
    parser_run.add_argument("--max-repair-attempts", type=int, default=3, help="Max repair attempts allowed")

    # compile
    parser_compile = subparsers.add_parser("compile", help="Compile drafts into single manuscript")
    parser_compile.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_compile.add_argument("--output", help="Output Markdown path")
    parser_compile.add_argument("--no-title", action="store_true", help="Do not prepend book title")
    parser_compile.add_argument(
        "--formatted-doc",
        action="store_true",
        help="Generate a formatted Word .docx manuscript with title page and contents",
    )

    # pacing
    parser_pacing = subparsers.add_parser("pacing", help="Generate a source-locked chapter pacing plan")
    parser_pacing.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_pacing.add_argument("--reference-analysis", help="Optional reference pacing calibration file")

    # packet
    parser_packet = subparsers.add_parser("packet", help="Render a context packet for a chapter")
    parser_packet.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_packet.add_argument("--chapter", required=True, help="Chapter slug (e.g. chapter-01 or epilogue)")
    parser_packet.add_argument(
        "--task",
        default="all",
        choices=["all", "draft-prose", "continuity-check", "extract-memory", "revise-style", "validate-change"],
        help="Task-specific context packet type (default: all)"
    )

    # tui
    subparsers.add_parser("tui", help="Launch interactive Terminal User Interface (TUI)")

    # analytics
    parser_analytics = subparsers.add_parser("analytics", help="Show file size metrics and cumulative token usage")
    parser_analytics.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # log-run
    parser_log = subparsers.add_parser("log-run", help="Log token metrics for an LLM run manually or programmatically")
    parser_log.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_log.add_argument("--model", required=True, help="LLM Model used (e.g. gpt-4o, claude-3-5-sonnet)")
    parser_log.add_argument("--input-tokens", type=int, required=True, help="Number of prompt/input tokens")
    parser_log.add_argument("--output-tokens", type=int, required=True, help="Number of completion/output tokens")
    parser_log.add_argument("--action", default="orchestration", help="Action performed (e.g., validate, draft, repair)")

    # init-action
    parser_init_action = subparsers.add_parser("init-action", help="Initialize a combat action plan template")
    parser_init_action.add_argument("chapter_folder", help="Path to chapter folder (e.g. books/my-book/chapters/chapter-01)")
    parser_init_action.add_argument("--scene", required=True, help="Scene ID or name (e.g. scene-2)")

    # check-persona
    parser_check_persona = subparsers.add_parser("check-persona", help="Validate an LLM call against the persona registry")
    parser_check_persona.add_argument("book_folder", help="Path to book folder")
    parser_check_persona.add_argument("--persona", required=True, help="Persona name (e.g., planner, writer, reviewer)")
    parser_check_persona.add_argument("--model", required=True, help="LLM model (e.g., gpt-4o)")
    parser_check_persona.add_argument("--action", required=True, help="Action being performed (e.g., draft)")
    parser_check_persona.add_argument("--projected-tokens", type=int, default=0, help="Projected prompt/input tokens")

    # repair
    parser_repair = subparsers.add_parser("repair", help="Run interactive repair wizard to fix scene logistics and inventory")
    parser_repair.add_argument("book_folder", help="Path to book folder")
    parser_repair.add_argument("chapter_slug", help="Slug of the chapter to repair (e.g., chapter-01)")

    # resolve-unknowns
    parser_resolve = subparsers.add_parser(
        "resolve-unknowns",
        help="Interactive Q&A wizard: answer all unresolved ## Unknowns items in rulebook.md to unblock the pipeline"
    )
    parser_resolve.add_argument(
        "book_folder",
        nargs="?",
        default="books/book-example",
        help="Path to book folder (default: books/book-example)"
    )

    # add-relation
    parser_add_rel = subparsers.add_parser("add-relation", help="Add a typed relationship between entities")
    parser_add_rel.add_argument("book_folder", help="Path to book folder")
    parser_add_rel.add_argument("subject", help="Subject entity (e.g. harlan)")
    parser_add_rel.add_argument("relation", help="Relationship type (e.g. distrusts)")
    parser_add_rel.add_argument("object", help="Object entity (e.g. darin)")
    parser_add_rel.add_argument("--source", default="manual", help="Source of relationship fact")

    # nlm subparser
    parser_nlm = subparsers.add_parser("nlm", help="Manage NotebookLM research integrations")
    nlm_subparsers = parser_nlm.add_subparsers(dest="nlm_command", required=True)

    # nlm list
    nlm_subparsers.add_parser("list", help="List available NotebookLM notebooks")

    # nlm status
    parser_nlm_status = nlm_subparsers.add_parser("status", help="Show NotebookLM integration status for a book")
    parser_nlm_status.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # nlm link
    parser_nlm_link = nlm_subparsers.add_parser("link", help="Link a NotebookLM notebook to a book folder")
    parser_nlm_link.add_argument("notebook_id", help="Notebook UUID")
    parser_nlm_link.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_nlm_link.add_argument("--title", help="Optional display title for the notebook")

    # nlm query
    parser_nlm_query = nlm_subparsers.add_parser("query", help="Query the linked NotebookLM notebook")
    parser_nlm_query.add_argument("query_text", help="Question to ask the notebook")
    parser_nlm_query.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # nlm sync-research
    parser_nlm_sync_res = nlm_subparsers.add_parser("sync-research", help="Sync facts from NotebookLM to research-pack.md")
    parser_nlm_sync_res.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # nlm sync-sources
    parser_nlm_sync_src = nlm_subparsers.add_parser("sync-sources", help="Upload local rules and drafts to NotebookLM")
    parser_nlm_sync_src.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # nlm generate-outline
    parser_nlm_gen_out = nlm_subparsers.add_parser("generate-outline", help="Create a unique notebook, upload sources, and query to generate outline")
    parser_nlm_gen_out.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # canon
    parser_canon = subparsers.add_parser("canon", help="Event-sourced canon fold engine and checks")
    canon_subparsers = parser_canon.add_subparsers(dest="canon_command", required=True)

    # canon build
    parser_canon_build = canon_subparsers.add_parser("build", help="Fold all events to build the current state snapshot")
    parser_canon_build.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # canon validate
    parser_canon_validate = canon_subparsers.add_parser("validate", help="Validate entity schemas and sequence history")
    parser_canon_validate.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # validate
    parser_validate = subparsers.add_parser("validate", help="Run full deterministic, style, and canon validations")
    parser_validate.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_validate.add_argument("--chapter", help="Chapter ID to restrict checks (e.g. chapter-01)")
    parser_validate.add_argument("--review-prompt", action="store_true", help="Generate AI semantic review prompt")

    # apply
    parser_apply = subparsers.add_parser("apply", help="Gate command: apply transitions and append chapter events")
    apply_subparsers = parser_apply.add_subparsers(dest="apply_command", required=True)
    parser_apply_change = apply_subparsers.add_parser("change", help="Parse, validate, and append chapter mutations")
    parser_apply_change.add_argument("book_folder", help="Path to book folder")
    parser_apply_change.add_argument("chapter_id", help="Chapter ID (e.g., chapter-01)")

    # migrate
    parser_migrate = subparsers.add_parser("migrate", help="Migrate legacy book assets to event-sourced structures")
    parser_migrate.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # memory
    parser_memory = subparsers.add_parser("memory", help="Persistent Memory Tier (build, retrieve, resolve, learn, apply-learning, serve)")
    memory_subparsers = parser_memory.add_subparsers(dest="memory_command", required=True)

    # memory build
    parser_mem_build = memory_subparsers.add_parser("build", help="Build memory index from book assets")
    parser_mem_build.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # memory retrieve
    parser_mem_retrieve = memory_subparsers.add_parser("retrieve", help="Query the persistent memory index")
    parser_mem_retrieve.add_argument("query", help="Text query to search for")
    parser_mem_retrieve.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_mem_retrieve.add_argument("--limit", type=int, default=10, help="Max results to return")

    # memory resolve
    parser_mem_resolve = memory_subparsers.add_parser("resolve", help="Resolve name to canonical ID")
    parser_mem_resolve.add_argument("name", help="Name or alias to resolve")
    parser_mem_resolve.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # memory learn
    parser_mem_learn = memory_subparsers.add_parser("learn", help="Analyze failed session logs to suggest corrective rules")
    parser_mem_learn.add_argument("log_file", help="Path to log file (or '-' for stdin)")
    parser_mem_learn.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # memory apply-learning
    parser_mem_apply = memory_subparsers.add_parser("apply-learning", help="Apply proposed rules to rulebook/instructions")
    parser_mem_apply.add_argument("proposal_id", help="Proposal UUID to apply")
    parser_mem_apply.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # memory serve
    parser_mem_serve = memory_subparsers.add_parser("serve", help="Serve memory MCP tools over stdio/HTTP")
    parser_mem_serve.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_mem_serve.add_argument("--port", type=int, default=8000, help="HTTP server port")
    parser_mem_serve.add_argument("--http", action="store_true", help="Run HTTP server instead of stdio")

    # checkpoint
    parser_checkpoint = subparsers.add_parser("checkpoint", help="Local checkpoint stashing (save, load, diff, restore)")
    checkpoint_subparsers = parser_checkpoint.add_subparsers(dest="checkpoint_command", required=True)

    # checkpoint save
    parser_chk_save = checkpoint_subparsers.add_parser("save", help="Save current changes to a named checkpoint")
    parser_chk_save.add_argument("name", help="Name of the checkpoint")
    parser_chk_save.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # checkpoint load
    parser_chk_load = checkpoint_subparsers.add_parser("load", help="Load/restore changes from a named checkpoint")
    parser_chk_load.add_argument("name", help="Name of the checkpoint")
    parser_chk_load.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # checkpoint restore
    parser_chk_restore = checkpoint_subparsers.add_parser("restore", help="Reset/restore changes to match a named checkpoint")
    parser_chk_restore.add_argument("name", help="Name of the checkpoint")
    parser_chk_restore.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # checkpoint diff
    parser_chk_diff = checkpoint_subparsers.add_parser("diff", help="Show differences between current changes and a named checkpoint")
    parser_chk_diff.add_argument("name", help="Name of the checkpoint")
    parser_chk_diff.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # scene
    parser_scene = subparsers.add_parser("scene", help="Scene-level authoring and manifest commands")
    scene_subparsers = parser_scene.add_subparsers(dest="scene_command", required=True)

    # scene init
    parser_scene_init = scene_subparsers.add_parser("init", help="Initialize a new scene manifest")
    parser_scene_init.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_scene_init.add_argument("--scene-id", "--scene", dest="scene_id", required=True, help="Scene ID (e.g. scene-01, ch01_sc01)")
    parser_scene_init.add_argument("--chapter", help="Chapter slug (optional if encoded in scene-id)")
    parser_scene_init.add_argument("--target-words", type=int, default=3500, help="Target word count for the scene")

    # scene packet
    parser_scene_packet = scene_subparsers.add_parser("packet", help="Generate a targeted scene context packet")
    parser_scene_packet.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_scene_packet.add_argument("--scene-id", "--scene", dest="scene_id", required=True, help="Scene ID (e.g. scene-01, ch01_sc01)")
    parser_scene_packet.add_argument("--chapter", help="Chapter slug (optional if encoded in scene-id)")

    # scene report
    parser_scene_report = scene_subparsers.add_parser("report", help="Generate scene metrics report")
    parser_scene_report.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_scene_report.add_argument("chapter", nargs="?", help="Chapter slug (e.g. chapter-08)")
    parser_scene_report.add_argument("scene_id", nargs="?", help="Scene ID (e.g. scene-02)")

    # patch
    parser_patch = subparsers.add_parser("patch", help="Patch building and splicing commands")
    # For top-level patch calls like: bf patch --chapter chapter-08 --scene scene-02
    parser_patch.add_argument("--scene", help="Scene ID (e.g. scene-02)")
    parser_patch.add_argument("--chapter", help="Chapter ID")
    parser_patch.add_argument("--failed-rules", nargs="+", help="Failed rules for top-level patch build")
    patch_subparsers = parser_patch.add_subparsers(dest="patch_command", required=False)

    # patch build
    parser_patch_build = patch_subparsers.add_parser("build", help="Build a small patch packet for failed rules")
    parser_patch_build.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_patch_build.add_argument("--scene-id", "--scene", dest="scene_id", required=True, help="Scene ID (e.g. scene-01, ch01_sc01)")
    parser_patch_build.add_argument("--chapter", help="Chapter slug (optional if encoded in scene-id)")
    parser_patch_build.add_argument("--failed-rules", nargs="+", help="List of failed rules or issues to patch")

    # patch splice
    parser_patch_splice = patch_subparsers.add_parser("splice", help="Splice replacement prose into original draft")
    parser_patch_splice.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_patch_splice.add_argument("--scene-id", "--scene", dest="scene_id", required=True, help="Scene ID (e.g. scene-01, ch01_sc01)")
    parser_patch_splice.add_argument("--chapter", help="Chapter slug (optional if encoded in scene-id)")

    # patch apply
    parser_patch_apply = patch_subparsers.add_parser("apply", help="Apply replacement patch (alias for splice)")
    parser_patch_apply.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_patch_apply.add_argument("--scene-id", "--scene", dest="scene_id", required=True, help="Scene ID (e.g. scene-01, ch01_sc01)")
    parser_patch_apply.add_argument("--chapter", help="Chapter slug (optional if encoded in scene-id)")
    parser_patch_apply.add_argument("--from-file", help="Path to replacement file")

    # queue
    parser_queue = subparsers.add_parser("queue", help="Central scene execution queue commands")
    queue_subparsers = parser_queue.add_subparsers(dest="queue_command", required=True)

    # queue build
    parser_queue_build = queue_subparsers.add_parser("build", help="Build or compile the scene queue")
    parser_queue_build.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # queue show
    parser_queue_show = queue_subparsers.add_parser("show", help="Display the scene queue status")
    parser_queue_show.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")

    # queue update
    parser_queue_update = queue_subparsers.add_parser("update", help="Update scene attributes in the queue")
    parser_queue_update.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder")
    parser_queue_update.add_argument("scene_key", help="Scene key in format chapter/scene (e.g. chapter-08/scene-02)")
    parser_queue_update.add_argument("--status", help="New status value")
    parser_queue_update.add_argument("--provider", help="New provider value")
    parser_queue_update.add_argument("--inc-generation", action="store_true", help="Increment generation attempts")
    parser_queue_update.add_argument("--inc-patch", action="store_true", help="Increment patch attempts")

    args = parser.parse_args()

    if not args.command:
        # Default to the status command's book-selection prompt instead of the
        # POSIX-only TUI, which crashes on Windows.
        args.command = "status"
        args.book_folder = None

    commands = {
        "init": cmd_init,
        "status": cmd_status,
        "run-loop": cmd_run_loop,
        "compile": cmd_compile,
        "pacing": cmd_pacing,
        "packet": cmd_packet,
        "tui": cmd_tui,
        "analytics": cmd_analytics,
        "log-run": cmd_log_run,
        "init-action": cmd_init_action,
        "check-persona": cmd_check_persona,
        "repair": cmd_repair,
        "add-relation": cmd_add_relation,
        "nlm": cmd_nlm,
        "resolve-unknowns": cmd_resolve_unknowns,
        "canon": cmd_canon,
        "validate": cmd_validate,
        "apply": cmd_apply,
        "migrate": cmd_migrate,
        "memory": cmd_memory,
        "checkpoint": cmd_checkpoint,
        "scene": cmd_scene,
        "patch": cmd_patch,
        "queue": cmd_queue,
    }

    try:
        return commands[args.command](args)
    except Exception as e:
        # Intentional catch-all top-level application crash barrier to gracefully log
        # execution failures and exit cleanly with status code 1.
        print(f"Execution Error: {e}", file=sys.stderr)
        return 1




if __name__ == "__main__":
    sys.exit(main())
