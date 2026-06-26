#!/usr/bin/env bash
set -euo pipefail

repo=""
workspace=""
mode=""

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
    --list)
      mode="list"
      shift
      ;;
    --open)
      mode="open"
      shift
      ;;
    --create)
      mode="create"
      shift
      ;;
    --ensure)
      mode="ensure"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage:
  chatgpt_workspace.sh --repo /abs/path/to/provider-web-driver-mcp --list
  chatgpt_workspace.sh --repo /abs/path/to/provider-web-driver-mcp --workspace "name" --open
  chatgpt_workspace.sh --repo /abs/path/to/provider-web-driver-mcp --workspace "name" --create
  chatgpt_workspace.sh --repo /abs/path/to/provider-web-driver-mcp --workspace "name" --ensure
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$repo" || -z "$mode" ]]; then
  echo "Missing required arguments. Use --help." >&2
  exit 2
fi

if [[ "$mode" != "list" && -z "$workspace" ]]; then
  echo "--workspace is required for mode '$mode'." >&2
  exit 2
fi

REPO="$repo" WORKSPACE_NAME="$workspace" MODE="$mode" \
node --import tsx <<'EOF'
const repo = process.env.REPO;
const workspace = process.env.WORKSPACE_NAME || "";
const mode = process.env.MODE;

if (!repo || !mode) {
  console.error("Missing environment variables.");
  process.exit(2);
}

const { launchBrowser } = await import(`${repo}/src/browser/launch.ts`);
const { findOrCreateTab } = await import(`${repo}/src/browser/page.ts`);

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

const context = await launchBrowser("chatgpt");
try {
  const page = await findOrCreateTab(context, "chatgpt.com");
  await gotoProjects(page);
  const workspacesBefore = await getWorkspaceNames(page);

  if (mode === "list") {
    console.log(JSON.stringify({ ok: true, provider: "chatgpt", workspaces: workspacesBefore }, null, 2));
    process.exit(0);
  }

  const existsBefore = workspacesBefore.includes(workspace);
  let created = false;
  let opened = false;

  if (mode === "create") {
    if (!existsBefore) {
      await createWorkspace(page, workspace);
      created = true;
    }
  } else if (mode === "ensure") {
    if (!existsBefore) {
      await createWorkspace(page, workspace);
      created = true;
    }
    if (!page.url().includes("/project")) {
      await gotoProjects(page);
      await openWorkspace(page, workspace);
    }
    opened = true;
  } else if (mode === "open") {
    if (!existsBefore) {
      console.error(JSON.stringify({ ok: false, error: `Workspace not found: ${workspace}` }, null, 2));
      process.exit(4);
    }
    await openWorkspace(page, workspace);
    opened = true;
  }

  if (mode === "create" && created && !page.url().includes("/project")) {
    await gotoProjects(page);
    await openWorkspace(page, workspace);
    opened = true;
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        provider: "chatgpt",
        workspaces_before: workspacesBefore,
        workspace_name: workspace,
        exists_before: existsBefore,
        created,
        opened,
        project_url: page.url(),
      },
      null,
      2,
    ),
  );
} finally {
  await context.close();
}
EOF
