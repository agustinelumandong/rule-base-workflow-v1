#!/usr/bin/env bash
set -euo pipefail

repo=""
workspace=""
prompt=""
timeout_ms="600000"
ensure_workspace="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --workspace)
      workspace="${2:-}"
      shift 2
      ;;
    --ensure-workspace)
      ensure_workspace="true"
      shift
      ;;
    --prompt)
      prompt="${2:-}"
      shift 2
      ;;
    --timeout-ms)
      timeout_ms="${2:-}"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage:
  chatgpt_chat.sh --repo /abs/path/to/provider-web-driver-mcp --prompt "text" [--timeout-ms 600000]
  chatgpt_chat.sh --repo /abs/path/to/provider-web-driver-mcp --workspace "name" --ensure-workspace --prompt "text"
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$repo" || -z "$prompt" ]]; then
  echo "Missing required arguments. Use --help." >&2
  exit 2
fi

REPO="$repo" WORKSPACE_NAME="$workspace" PROMPT_TEXT="$prompt" TIMEOUT_MS="$timeout_ms" ENSURE_WORKSPACE="$ensure_workspace" \
node --import tsx <<'EOF'
const repo = process.env.REPO;
const workspace = process.env.WORKSPACE_NAME || "";
const prompt = process.env.PROMPT_TEXT;
const timeoutMs = Number(process.env.TIMEOUT_MS || "600000");
const ensureWorkspace = process.env.ENSURE_WORKSPACE === "true";

if (!repo || !prompt) {
  console.error("Missing environment variables.");
  process.exit(2);
}

const { launchBrowser } = await import(`${repo}/src/browser/launch.ts`);
const { findOrCreateTab } = await import(`${repo}/src/browser/page.ts`);
const { submitPrompt } = await import(`${repo}/src/providers/chatgpt/prompt.ts`);

async function getWorkspaceNames(page) {
  return page.evaluate(() =>
    Array.from(document.querySelectorAll('[role="row"].group.EhAptG_selectableRow'))
      .map((el) => {
        const txt = (el.textContent || "").trim();
        return txt
          .replace(/Today(?:Today)*/g, "")
          .replace(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}.*/s, "")
          .trim();
      })
      .filter(Boolean),
  );
}

async function gotoProjects(page) {
  await page.goto("https://chatgpt.com/projects", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(2500);
}

async function createWorkspace(page, name) {
  const newProjectButton = page.getByLabel("New project").first();
  if (await newProjectButton.isVisible().catch(() => false)) {
    await newProjectButton.click({ force: true });
  } else {
    await page.getByRole("button", { name: "New" }).first().click({ force: true });
  }

  const nameInput = page.locator('input[name="projectName"], #project-name').first();
  await nameInput.waitFor({ state: "visible", timeout: 10000 });
  await nameInput.fill(name);
  await page.getByRole("button", { name: "Create project" }).first().click({ force: true });
  await page.waitForTimeout(3000);
}

async function openWorkspace(page, name) {
  const sidebarProject = page.getByRole("button", { name, exact: true }).first();
  if (await sidebarProject.isVisible().catch(() => false)) {
    await sidebarProject.click({ force: true });
    await page.waitForTimeout(2000);
  }
  if (page.url().includes("/projects")) {
    const row = page.locator('[role="row"].group.EhAptG_selectableRow').filter({ hasText: name }).first();
    await row.waitFor({ state: "visible", timeout: 15000 });
    await row.click({ force: true });
    await page.waitForTimeout(2000);
  }
}

async function getLatestAssistantText(page) {
  return page.evaluate(() => {
    const selectors = [
      '[data-message-author-role="assistant"]',
      'article[data-testid^="conversation-turn-"] .markdown',
      'div[data-message-id] .markdown',
      '.markdown',
    ];

    const isVisible = (el) => {
      if (!(el instanceof HTMLElement)) return false;
      if (el.hidden) return false;
      const style = window.getComputedStyle(el);
      if (style.display === "none" || style.visibility === "hidden") return false;
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    };

    for (const selector of selectors) {
      const nodes = Array.from(document.querySelectorAll(selector));
      if (!nodes.length) continue;
      const visible = nodes.filter(isVisible);
      const last = (visible.length ? visible : nodes).at(-1);
      const text = (last?.innerText || last?.textContent || "").trim();
      if (text) return text;
    }
    return "";
  });
}

async function waitForStableResponse(page, waitMs) {
  const start = Date.now();
  let last = "";
  let stable = 0;

  while (Date.now() - start < waitMs) {
    const streaming = await page
      .locator('button[aria-label="Stop streaming"]')
      .first()
      .isVisible()
      .catch(() => false);
    const text = await getLatestAssistantText(page);

    if (!streaming && text && text === last) {
      stable += 1;
      if (stable >= 3) {
        return { completed: true, response_text: text, elapsed_ms: Date.now() - start };
      }
    } else {
      if (text !== last) last = text;
      stable = 0;
    }

    await page.waitForTimeout(1000);
  }

  return { completed: false, response_text: last, elapsed_ms: Date.now() - start };
}

const context = await launchBrowser("chatgpt");
try {
  const page = await findOrCreateTab(context, "chatgpt.com");
  let created = false;

  if (workspace) {
    await gotoProjects(page);
    const workspacesBefore = await getWorkspaceNames(page);
    const existsBefore = workspacesBefore.includes(workspace);

    if (!existsBefore) {
      if (!ensureWorkspace) {
        console.error(JSON.stringify({ ok: false, error: `Workspace not found: ${workspace}` }, null, 2));
        process.exit(4);
      }
      await createWorkspace(page, workspace);
      created = true;
    }

    if (!page.url().includes("/project")) {
      await gotoProjects(page);
      await openWorkspace(page, workspace);
    }
  } else {
    await page.goto("https://chatgpt.com/", { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForTimeout(2500);
  }

  const composer = page
    .locator('#prompt-textarea, [data-testid="composer-input"], div.ProseMirror[contenteditable="true"]')
    .first();
  const composerVisible = await composer.isVisible().catch(() => false);
  if (!composerVisible) {
    const newChatLink = page.getByRole("link", { name: "New chat" }).first();
    const newChatButton = page.getByRole("button", { name: "New chat" }).first();
    if (await newChatLink.isVisible().catch(() => false)) {
      await newChatLink.click({ force: true });
      await page.waitForTimeout(2000);
    } else if (await newChatButton.isVisible().catch(() => false)) {
      await newChatButton.click({ force: true });
      await page.waitForTimeout(2000);
    }
  }

  const send = await submitPrompt(page, prompt);
  if (!send.sent) {
    console.error(JSON.stringify({ ok: false, stage: "send", error: send.error || "Failed to send prompt" }, null, 2));
    process.exit(5);
  }

  const waited = await waitForStableResponse(page, timeoutMs);
  if (!waited.completed) {
    console.error(JSON.stringify({ ok: false, stage: "wait", ...waited }, null, 2));
    process.exit(6);
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        provider: "chatgpt",
        workspace_name: workspace || undefined,
        created_workspace: created,
        response_text: waited.response_text,
        page_url: page.url(),
      },
      null,
      2,
    ),
  );
} finally {
  await context.close();
}
EOF
