#!/usr/bin/env python3
# =============================================================================
# Project Install / Repair Script — current-workflow
#
# Usage:
#   python scripts/install.py           # Detect and fix all missing components
#   python scripts/install.py --dry-run # Show what would be installed, no action
#   python scripts/install.py --force   # Reinstall everything even if present
# =============================================================================

import sys
import os
import shutil
import subprocess
import argparse
import importlib.util
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="BookForge installer and repair tool.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without executing them.")
    parser.add_argument("--force", action="store_true", help="Reinstall all components even if present.")
    return parser.parse_args()

def print_banner(dry_run, force, proj_root):
    print("\n╔══════════════════════════════════════════════════════╗")
    if dry_run:
        print("║    current-workflow — Install (DRY RUN)              ║")
    else:
        print("║       current-workflow — Install / Repair            ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"  Project: {proj_root}")
    if dry_run:
        print("  Mode:    --dry-run (no changes will be made)")
    if force:
        print("  Mode:    --force (reinstalling everything)")
    print("")

def run_or_dry(label, cmd, dry_run=False, capture=True):
    if dry_run:
        print(f"  [dry-run]  {label}")
        print(f"             → {' '.join(cmd)}")
        return True
    else:
        print(f"  ⚙️   {label}")
        try:
            if capture:
                res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                res = subprocess.run(cmd, check=True)
            print("  ✅  Done\n")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  ❌  Failed: {' '.join(cmd)}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"      Error: {e.stderr.decode('utf-8', errors='ignore').strip()}")
            print("")
            return False

def check_command(cmd):
    return shutil.which(cmd) is not None

def main():
    args = parse_args()
    proj_root = Path(__file__).resolve().parents[1]
    
    print_banner(args.dry_run, args.force, proj_root)
    
    installed_count = 0
    skipped_count = 0
    manual_count = 0
    error_count = 0
    
    # ── Section 1: System prerequisites ──────────────────────────────────────────
    print(f"\n── 1. System Prerequisites {'─' * 30}")
    
    # Python Version >= 3.8
    py_version = sys.version_info
    if py_version >= (3, 8):
        print(f"  ✅  Already installed — Python {sys.version.split()[0]} (≥3.8)")
        skipped_count += 1
    else:
        print(f"  ⚠️   Manual required — Python too old ({sys.version.split()[0]}) — install ≥3.8 via pyenv/mise/system")
        manual_count += 1
        
    # uv
    if check_command("uv"):
        # Get uv version
        try:
            uv_ver_res = subprocess.run(["uv", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            uv_ver = uv_ver_res.stdout.strip().split("\n")[0]
        except Exception:
            uv_ver = "unknown version"
        print(f"  ✅  Already installed — uv ({uv_ver})")
        skipped_count += 1
    else:
        print("  ⚠️   uv not found — needed for NotebookLM MCP")
        print("       Install with:")
        print("         curl -LsSf https://astral.sh/uv/install.sh | sh  (Unix)")
        print("         irm https://astral.sh/uv/install.ps1 | iex    (Windows)")
        manual_count += 1
        
    # git
    if check_command("git"):
        try:
            git_ver_res = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            git_ver = git_ver_res.stdout.strip()
        except Exception:
            git_ver = "unknown version"
        print(f"  ✅  Already installed — git ({git_ver})")
        skipped_count += 1
    else:
        print("  ⚠️   git not found — install via system package manager or from git-scm.com")
        manual_count += 1
        
    # ── Section 2: BookForge Package ──────────────────────────────────────────────
    print(f"\n── 2. BookForge Package {'─' * 35}")
    
    bf_installed = importlib.util.find_spec("bookforge") is not None
    if bf_installed and not args.force:
        print("  ✅  Already installed — bookforge package")
        skipped_count += 1
    else:
        setup_file = proj_root / "setup.py"
        if not setup_file.exists():
            print(f"  ❌  setup.py not found in {proj_root} — cannot install bookforge")
            error_count += 1
        else:
            success = run_or_dry(
                "Installing bookforge (pip install -e .)",
                [sys.executable, "-m", "pip", "install", "-e", str(proj_root)],
                dry_run=args.dry_run
            )
            if success:
                installed_count += 1
            else:
                error_count += 1
                
    # ── Section 3: Agent Skills ───────────────────────────────────────────────────
    print(f"\n── 3. Agent Skills (.agents/skills/) {'─' * 22}")
    
    skills_dir = proj_root / ".agents" / "skills"
    required_skills = [
        "commit-prompt",
        "humanizer",
        "manuscript-workflow-orchestrator",
        "pig-prompt",
        "western-classic-writing-style",
        "western-historical-writing-style",
        "western-manuscript-style",
        "western-outlaw-writing-style",
        "western-revisionist-writing-style",
        "western-romance-writing-style",
        "western-story-pattern-analyzer",
        "western-weird-writing-style",
    ]
    
    missing_skills = []
    for skill in required_skills:
        skill_file = skills_dir / skill / "SKILL.md"
        if not skill_file.exists():
            missing_skills.append(skill)
            
    if not missing_skills:
        print(f"  ✅  All {len(required_skills)} skill folders present")
        skipped_count += 1
    else:
        print(f"  ❌  Missing {len(missing_skills)} skill(s):")
        for s in missing_skills:
            print(f"       - {s}")
        print("  ⚠️   Skill folders are part of the git repository. Restore with:")
        print("         git restore .agents/skills/")
        manual_count += 1
        
    # ── Section 4: Orchestrator CLI (bf) ─────────────────────────────────────────
    print(f"\n── 4. Orchestrator CLI (bf) {'─' * 35}")

    # Legacy orchestrator scripts have been removed; the unified `bf` CLI is now
    # the sole entry surface. Verify the key subcommands are registered.
    required_cmds = [
        "init", "status", "validate", "compile", "pacing", "packet",
        "run-loop", "resolve-unknowns", "canon", "apply", "memory", "checkpoint",
    ]

    missing_cmds = []
    for cmd in required_cmds:
        # Prefer the installed `bf` entrypoint; fall back to the module form.
        import subprocess
        bf_check = subprocess.run(
            ["bf", cmd, "--help"], capture_output=True
        ) if shutil.which("bf") else None
        if bf_check and bf_check.returncode == 0:
            continue
        mod_check = subprocess.run(
            [sys.executable, "-m", "bookforge.cli", cmd, "--help"],
            capture_output=True,
        )
        if mod_check.returncode != 0:
            missing_cmds.append(cmd)

    if not missing_cmds:
        print(f"  ✅  All {len(required_cmds)} bf subcommands available")
        skipped_count += 1
    else:
        print(f"  ❌  Missing {len(missing_cmds)} bf subcommand(s):")
        for c in missing_cmds:
            print(f"       - bf {c}")
        print("  ⚠️   Reinstall bookforge (pip install -e .) to register the bf entrypoint.")
        manual_count += 1
        
    # ── Section 5: Headroom (Context Compression) ─────────────────────────────────
    print(f"\n── 5. Headroom (Context Compression) {'─' * 22}")
    
    # Try importing bookforge headroom module
    try:
        sys.path.insert(0, str(proj_root))
        from bookforge.core.headroom import HAS_OFFICIAL_HEADROOM
        print("  ✅  bookforge.core.headroom (built-in, importable)")
        skipped_count += 1
    except Exception:
        print("  ❌  bookforge.core.headroom not importable — bookforge may not be installed")
        print("       → Re-run Section 2 installation")
        error_count += 1
        HAS_OFFICIAL_HEADROOM = False
        
    # headroom-ai enhanced compression package
    headroom_installed = importlib.util.find_spec("headroom") is not None
    if headroom_installed and not args.force:
        print("  ✅  headroom-ai (enhanced compression) already installed")
        skipped_count += 1
    else:
        success = run_or_dry(
            "Installing headroom-ai (enhanced compression)",
            [sys.executable, "-m", "pip", "install", "headroom-ai"],
            dry_run=args.dry_run
        )
        if success:
            installed_count += 1
        else:
            error_count += 1
            
    # ── Section 6: Test Runner (pytest) ───────────────────────────────────────────
    print(f"\n── 6. Test Runner (pytest) {'─' * 32}")
    
    pytest_installed = importlib.util.find_spec("pytest") is not None
    if pytest_installed and not args.force:
        print("  ✅  pytest already installed")
        skipped_count += 1
    else:
        success = run_or_dry(
            "Installing pytest",
            [sys.executable, "-m", "pip", "install", "pytest"],
            dry_run=args.dry_run
        )
        if success:
            installed_count += 1
        else:
            error_count += 1
            
    # ── Section 7: NotebookLM MCP ─────────────────────────────────────────────────
    print(f"\n── 7. NotebookLM MCP {'─' * 38}")
    
    if not check_command("uv"):
        print("  ⏭️   Skipping NotebookLM MCP — uv not available (see Section 1)")
    else:
        # 7a. Package installation
        nlm_mcp_installed = False
        try:
            tool_list = subprocess.run(["uv", "tool", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "notebooklm-mcp-cli" in tool_list.stdout:
                nlm_mcp_installed = True
        except Exception:
            pass
            
        if nlm_mcp_installed and not args.force:
            print("  ✅  notebooklm-mcp-cli tool already installed")
            skipped_count += 1
        else:
            cmd = ["uv", "tool", "install", "notebooklm-mcp-cli"]
            if args.force:
                cmd.append("--force")
            success = run_or_dry("Installing notebooklm-mcp-cli tool", cmd, dry_run=args.dry_run)
            if success:
                installed_count += 1
            else:
                error_count += 1
                
        # 7b. Auth validation
        auth_file = Path.home() / ".notebooklm-mcp-cli" / "profiles" / "default" / "cookies.json"
        auth_valid = False
        if auth_file.exists() and not args.force:
            try:
                # nlm login --check
                auth_check = subprocess.run(["nlm", "login", "--check"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if any(x in auth_check.stdout.lower() for x in ("authenticated", "valid", "✓", "success")):
                    print("  ✅  NotebookLM Auth is valid")
                    skipped_count += 1
                    auth_valid = True
            except Exception:
                pass
                
        if not auth_valid:
            print("  ⚠️   NotebookLM authentication is missing or expired.")
            if args.dry_run:
                print("  [dry-run]  Would run interactive: nlm login")
            else:
                print("  ⚙️   Re-authenticating (browser window will open)...")
                try:
                    subprocess.run(["nlm", "login"], check=True)
                    print("  ✅  NotebookLM Auth complete\n")
                    installed_count += 1
                except Exception as e:
                    print(f"  ❌  Auth failed: {e}. Please run `nlm login` manually.")
                    error_count += 1
                    
        # 7c. Antigravity MCP registration
        mcp_config_path = Path.home() / ".gemini" / "antigravity" / "mcp_config.json"
        config_registered = False
        if mcp_config_path.exists() and not args.force:
            try:
                config_content = mcp_config_path.read_text(encoding="utf-8")
                if "notebooklm" in config_content:
                    print("  ✅  NotebookLM MCP registered in Antigravity mcp_config.json")
                    skipped_count += 1
                    config_registered = True
            except Exception:
                pass
                
        if not config_registered:
            success = run_or_dry(
                "Registering NotebookLM MCP with Antigravity",
                ["nlm", "setup", "add", "antigravity"],
                dry_run=args.dry_run
            )
            if success:
                installed_count += 1
            else:
                error_count += 1
                
        # 7d. AI Skill Installation
        skill_file = Path.home() / ".gemini" / "antigravity" / "skills" / "nlm-skill" / "SKILL.md"
        skill_installed = False
        if skill_file.exists() and not args.force:
            print("  ✅  NotebookLM AI skill installed in Antigravity")
            skipped_count += 1
            skill_installed = True
            
        if not skill_installed:
            success = run_or_dry(
                "Installing NotebookLM AI skill with Antigravity",
                ["nlm", "skill", "install", "antigravity"],
                dry_run=args.dry_run
            )
            if success:
                installed_count += 1
            else:
                error_count += 1
                
    # ── Summary ───────────────────────────────────────────────────────────────────
    print(f"\n╔══════════════════════════════════════════════════════╗")
    print(f"║                      Summary                         ║")
    print(f"╠══════════════════════════════════════════════════════╣")
    if args.dry_run:
        print("║  ℹ️   Dry run complete — no changes made.            ║")
        print("║      Re-run without --dry-run to apply.             ║")
    elif error_count > 0:
        print(f"║  ❌  {error_count} install error(s). Check output above.       ║")
    elif manual_count > 0 and installed_count == 0:
        print("║  ✅  Nothing to install — project is fully set up.  ║")
    elif installed_count > 0:
        print(f"║  ✅  {installed_count} component(s) installed/repaired.            ║")
    else:
        print("║  ✅  Nothing to install — project is fully set up.  ║")
        
    if manual_count > 0:
        print(f"║  ⚠️   {manual_count} item(s) need manual action (see above).       ║")
        
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Verify:  bf validate or python scripts/check.sh      ║")
    if not args.dry_run and installed_count > 0:
        print("║  Restart Antigravity (agy) to activate MCP.        ║")
    print("╚══════════════════════════════════════════════════════╝\n")

if __name__ == "__main__":
    main()
