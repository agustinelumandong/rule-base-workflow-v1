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
from bookforge import config


def cmd_init(args: argparse.Namespace) -> int:
    book_folder = Path(args.book_folder)
    if book_folder.exists() and any(book_folder.iterdir()):
        print(f"Error: Directory '{book_folder}' already exists and is not empty.", file=sys.stderr)
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

    # 2. Perform continuity carry-forward from a completed book if requested
    if hasattr(args, "carry_from") and args.carry_from:
        carry_from_path = Path(args.carry_from)
        carry_msg = series_module.carry_forward_book_continuity(carry_from_path, book_folder)
        print(carry_msg)

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



def main() -> int:
    parser = argparse.ArgumentParser(
        description="BookForge: A Production-Ready Manuscript Workflow Pipeline",
        prog="bookforge"
    )
    subparsers = parser.add_subparsers(dest="command", required=False)

    # init
    parser_init = subparsers.add_parser("init", help="Initialize a new book structure")
    parser_init.add_argument("book_folder", help="Path to book folder (e.g. books/my-book)")
    parser_init.add_argument("--carry-from", help="Optional path to completed prior book in the series")

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

    # analytics
    parser_analytics = subparsers.add_parser("analytics", help="Show file size metrics and cumulative token usage")
    parser_analytics.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")

    # log-run
    parser_log = subparsers.add_parser("log-run", help="Log token metrics for an LLM run manually or programmatically")
    parser_log.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")
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
        default="books/tex-cade",
        help="Path to book folder (default: books/tex-cade)"
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
    parser_nlm_status.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")

    # nlm link
    parser_nlm_link = nlm_subparsers.add_parser("link", help="Link a NotebookLM notebook to a book folder")
    parser_nlm_link.add_argument("notebook_id", help="Notebook UUID")
    parser_nlm_link.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")
    parser_nlm_link.add_argument("--title", help="Optional display title for the notebook")

    # nlm query
    parser_nlm_query = nlm_subparsers.add_parser("query", help="Query the linked NotebookLM notebook")
    parser_nlm_query.add_argument("query_text", help="Question to ask the notebook")
    parser_nlm_query.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")

    # nlm sync-research
    parser_nlm_sync_res = nlm_subparsers.add_parser("sync-research", help="Sync facts from NotebookLM to research-pack.md")
    parser_nlm_sync_res.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")

    # nlm sync-sources
    parser_nlm_sync_src = nlm_subparsers.add_parser("sync-sources", help="Upload local rules and drafts to NotebookLM")
    parser_nlm_sync_src.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")

    # nlm generate-outline
    parser_nlm_gen_out = nlm_subparsers.add_parser("generate-outline", help="Create a unique notebook, upload sources, and query to generate outline")
    parser_nlm_gen_out.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder")

    args = parser.parse_args()

    if not args.command:
        args.command = "tui"

    commands = {
        "init": cmd_init,
        "status": cmd_status,
        "run-loop": cmd_run_loop,
        "compile": cmd_compile,
        "tui": cmd_tui,
        "analytics": cmd_analytics,
        "log-run": cmd_log_run,
        "init-action": cmd_init_action,
        "check-persona": cmd_check_persona,
        "repair": cmd_repair,
        "add-relation": cmd_add_relation,
        "nlm": cmd_nlm,
        "resolve-unknowns": cmd_resolve_unknowns,
    }

    try:
        return commands[args.command](args)
    except Exception as e:
        print(f"Execution Error: {e}", file=sys.stderr)
        return 1




if __name__ == "__main__":
    sys.exit(main())
