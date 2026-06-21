# BookForge Real Provider Drafting Guide

**Status:** provider MVP guide
**Scope:** opt-in OpenAI drafting through the BookForge model-run boundary

BookForge keeps deterministic drafting as the default. OpenAI drafting is opt-in and requires both an environment gate and a command flag.

## Required Environment

```bash
export BOOKFORGE_ALLOW_EXTERNAL_MODELS=true
export OPENAI_API_KEY="sk-..."
```

Do not commit API keys or store them in project artifacts.

## Draft With OpenAI

Create or import an approved input artifact first, then run:

```bash
python bookforge/cli/app.py chapter draft my-real-book chapter-001-openai \
  --input-artifact artifact:my-real-book:chapter-001:v1 \
  --provider openai \
  --model gpt-4.1-mini \
  --allow-external-models \
  --root .bookforge-real
```

The command:

- reads approved input artifact text,
- sends it to OpenAI through the Responses API,
- creates a candidate revision artifact,
- records a model-run trace,
- keeps review approval as a separate step.

## Review And Export

Approve the candidate:

```bash
python bookforge/cli/app.py review approve my-real-book artifact:my-real-book:chapter-001-openai:v1 \
  --reviewer reviewer:local \
  --root .bookforge-real
```

Export the approved revision:

```bash
python bookforge/cli/app.py manuscript export my-real-book book-1 \
  --chapter-artifact artifact:my-real-book:chapter-001-openai-approved:v1 \
  --output .bookforge-real/exports/my-real-book.md \
  --root .bookforge-real
```

## Safety Boundaries

- OpenAI is not the default provider.
- OpenAI drafting fails unless `BOOKFORGE_ALLOW_EXTERNAL_MODELS=true` and `--allow-external-models` are both present.
- Provider output is a candidate revision only.
- Human review still approves or rejects candidate artifacts.
- Deterministic tests use fake transports or deterministic adapters and do not require network access.
