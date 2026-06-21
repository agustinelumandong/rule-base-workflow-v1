# Git Commit Instructions

## [1. Role / Persona]
Act as an expert Senior Software Engineer. Your target audience is developers on the team.

## [2. Context]
I need to solve a problem regarding inconsistent, monolithic commits that make code review, blame, and changelog generation difficult. The goal is to provide value by establishing a disciplined atomic commit workflow that keeps the repository history clean, logical, and reversible.

## [3. Core Task]
Execute the following steps sequentially:

1. Run `git status` to identify all modified and untracked files.
2. Group files logically by feature, component, or purpose.
3. Stage each group individually using `git add <file1> <file2> ...`.
4. Commit the staged group with a descriptive conventional commit message.
5. Verify with `git status` and repeat for the next logical group.
6. Confirm the working tree is clean (except for purposely ignored files) when finished.

## [4. Constraints & Rules]
- **Tone:** Professional yet practical.
- **Atomicity:** Never commit unrelated changes together. Each commit must represent a single logical change.
- **Grouping:** Categorize files into logical buckets:
  - Core Logic (e.g., `bookforge/core/memory.py`)
  - CLI Command Layer (e.g., `bookforge/cli.py`)
  - Tests (e.g., `tests/test_memory.py`)
  - Configuration and Specifications (e.g., `spec/`)
  - Documentation and Shims (e.g., `AGENTS.md`, `README.md`)
- **Message Format:** Use `<type>(<scope>): <short description>` (e.g., `feat(core): implement persistent memory tier interfaces`).
- **Ambiguity:** If a file spans multiple features, stop and ask for guidance or use `git add -p` to stage specific hunks.

## [5. Output Format]
For each logical group, stage and commit as follows:

```bash
# Stage only the files belonging to one logical group
git add <file1> <file2>

# Commit with a descriptive message
git commit -m "<type>(<scope>): <short description>"
```

Example commit messages:
- `feat(core): implement persistent memory tier interfaces`
- `test(core): add unit tests for TF-IDF backend and resolve logic`
- `feat(cli): wire up bf memory subcommand group`
- `docs(readme): update installation instructions`

## [6. Example Workflow]

```bash
git status

# Stage and commit Core Logic
git add bookforge/core/memory.py bookforge/core/index.py
git commit -m "feat(core): add persistent memory tier interfaces"

# Stage and commit CLI Command Layer
git add bookforge/cli.py bookforge/commands/
git commit -m "feat(cli): wire up memory subcommand group"

# Stage and commit Tests
git add tests/test_memory.py tests/test_index.py
git commit -m "test(core): add unit tests for memory operations"

# Stage and commit Configuration
git add spec/ pyproject.toml
git commit -m "chore(spec): define memory tier接口 specification"

# Verify clean state
git status
```