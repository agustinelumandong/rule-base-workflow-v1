# BookForge First Real Book Workflow

**Status:** local author workflow MVP guide
**Scope:** create a real local project, import chapter text, approve candidate text, and export an approved manuscript

This guide uses real local files. It does not require a cloud AI provider. External model access remains disabled by default.

## 1. Create A Workspace

```bash
cd /home/cshan28/Dev/Projects/Experimental/BookForge
rm -rf .bookforge-real
mkdir -p local-input
```

## 2. Create Project And Book Records

```bash
python bookforge/cli/app.py project create my-real-book --root .bookforge-real
python bookforge/cli/app.py book create my-real-book book-1 --root .bookforge-real
```

Or create the project and first book from an author intake record:

```bash
python bookforge/cli/app.py project intake my-real-book book-1 \
  --title "Lone Star Reckoning" \
  --concept "A drifter hunts the Barrow gang across a winter range." \
  --constraint "Western tone" \
  --constraint "No modern slang" \
  --genre western \
  --audience adult \
  --root .bookforge-real
```

Create a draft story bible from the intake:

```bash
python bookforge/cli/app.py planning bible my-real-book book-1 \
  --character "Darin Mayweather" \
  --location "Abilene" \
  --theme "Justice costs restraint" \
  --canon-note "Darin carries a Colt revolver with three rounds." \
  --root .bookforge-real
```

Create a local outline from a JSON payload:

```bash
python bookforge/cli/app.py planning outline my-real-book book-1 \
  --file local-input/outline.json \
  --root .bookforge-real
```

Create a scene card against the saved outline:

```bash
python bookforge/cli/app.py planning scene-card my-real-book book-1 scene-001 \
  --chapter chapter-001 \
  --location "Abilene road" \
  --character "Darin Mayweather" \
  --goal "Darin reaches town." \
  --conflict "Fresh gang sign complicates the approach." \
  --reveal "The Barrow gang passed before dawn." \
  --state-change "Darin commits to entering Abilene." \
  --forbidden-event "Darin catches the gang" \
  --next-beat-connection "The livery scene follows the tracks." \
  --root .bookforge-real
```

## 3. Write A Real Chapter File

```bash
cat > local-input/chapter-001.md <<'EOF'
Chapter One

Cole Mercer rode into Abilene with dust on his coat and trouble waiting at the depot.
EOF
```

## 4. Import The Chapter

```bash
python bookforge/cli/app.py chapter import my-real-book book-1 chapter-001 \
  --number 1 \
  --title "Chapter One" \
  --file local-input/chapter-001.md \
  --root .bookforge-real
```

The command returns a `source_artifact_id`, for example:

```text
artifact:my-real-book:chapter-001:v1
```

## 4A. Import A Structured Manuscript

If your file already contains chapter headings, import the full manuscript structure instead:

```bash
python bookforge/cli/app.py manuscript import-structured my-real-book book-1 \
  --file local-input/chapter-001.md \
  --root .bookforge-real
```

This preserves chapter source offsets and creates approved preserved-original chapter artifacts for each `CHAPTER N` heading.

## 4B. Extract Reviewable Canon Proposals

After structured import, create reviewable story-bible, character, canon-fact, timeline, summary, object-state, state-fact, and continuity-lock proposals from the approved imported chapter artifact:

```bash
python bookforge/cli/app.py manuscript extract-canon my-real-book \
  --source-artifact artifact:my-real-book:chapter-001:v1 \
  --root .bookforge-real
```

Extraction creates proposed memory records only. It does not approve canon or promote story truth without review.

Supported explicit extraction markers are:

```text
Story Bible: Darin Mayweather is a cautious drifter hunting the Barrow gang.
Character: Darin Mayweather - cautious drifter with a scarred left hand.
Canon: Darin carries a Colt revolver with three rounds.
Summary: Darin reaches Abilene and learns the Barrow gang passed through town.
Timeline: Dawn - Darin enters Abilene from the north road.
Object: Colt Revolver - Darin carries it loaded with three rounds.
State: Darin.location = Abilene livery stable.
Lock: Darin.ammunition = 3 rounds (strict).
```

Approve a proposal only after review:

```bash
python bookforge/cli/app.py memory approve-proposal my-real-book memory-proposal:my-real-book:1 \
  --reviewer reviewer:local \
  --root .bookforge-real
```

Reject unsupported extracted truth instead of promoting it:

```bash
python bookforge/cli/app.py memory reject-proposal my-real-book memory-proposal:my-real-book:2 \
  --reviewer reviewer:local \
  --reason "unsupported by manuscript evidence" \
  --root .bookforge-real
```

## 5. Inspect Imported Content

```bash
python bookforge/cli/app.py chapter list my-real-book --root .bookforge-real
python bookforge/cli/app.py chapter show my-real-book artifact:my-real-book:chapter-001:v1 --root .bookforge-real
```

## 6. Assemble A Manuscript

Imported chapters are approved preserved originals, so they can be assembled immediately.

```bash
python bookforge/cli/app.py manuscript assemble my-real-book book-1 \
  --chapter-artifact artifact:my-real-book:chapter-001:v1 \
  --root .bookforge-real
```

## 7. Draft A Candidate Through The Deterministic Provider

The current public CLI supports deterministic local drafting. Write the generated output you want the local deterministic provider to return:

```bash
cat > local-input/chapter-001-draft.md <<'EOF'
Chapter One

Cole Mercer rode into Abilene under a hard noon sun, his coat gray with trail dust and trouble waiting beside the depot.
EOF
```

Run the draft command:

```bash
python bookforge/cli/app.py chapter draft my-real-book chapter-001-draft \
  --input-artifact artifact:my-real-book:chapter-001:v1 \
  --output-file local-input/chapter-001-draft.md \
  --root .bookforge-real
```

The command creates a candidate revision artifact and records a model-run trace through the deterministic provider boundary.

## 8. Review And Approve The Candidate

```bash
python bookforge/cli/app.py review approve my-real-book artifact:my-real-book:chapter-001-draft:v1 \
  --reviewer reviewer:local \
  --root .bookforge-real
```

The command records a review decision and creates a new approved revision artifact with the candidate text, for example:

```text
artifact:my-real-book:chapter-001-draft-approved:v1
```

## 9. Export The Manuscript

```bash
python bookforge/cli/app.py manuscript export my-real-book book-1 \
  --chapter-artifact artifact:my-real-book:chapter-001-draft-approved:v1 \
  --output .bookforge-real/exports/my-real-book.md \
  --root .bookforge-real
```

Open the exported file:

```bash
sed -n '1,120p' .bookforge-real/exports/my-real-book.md
```

## 10. Test The Same Workflow In The Browser

Install the browser test dependency once:

```bash
pip install -e ".[dev]"
python -m playwright install chromium
```

Run the automated ReviewDesk smoke flow:

```bash
python scripts/smoke_browser_workflow.py
```

Run it with a real local chapter file and save the browser-downloaded manuscript:

```bash
mkdir -p /tmp/bookforge-downloads
python scripts/smoke_browser_workflow.py \
  --chapter-file local-input/chapter-001.md \
  --download-dir /tmp/bookforge-downloads
```

To watch the browser while it creates the project, imports the chapter, drafts, approves, and exports:

```bash
python scripts/smoke_browser_workflow.py --headed
```

To keep the generated local storage for inspection:

```bash
python scripts/smoke_browser_workflow.py --storage-root .bookforge-browser-smoke --keep-storage
```

## Current Boundary

This workflow proves real local project/book/chapter/manuscript handling and deterministic provider-backed candidate drafting. OpenAI drafting is available as an explicit opt-in provider path; see `BOOKFORGE-REAL-PROVIDER-DRAFTING.md`.
