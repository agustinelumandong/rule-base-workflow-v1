# ChatGPT Workspace Workflow

## Purpose

Capture the live ChatGPT Projects workflow for workspace management only: list, open, and create.

## Supported operations

- List projects
- Open an existing project
- Create a missing project
- Ensure a project exists and is opened

## Current selectors and behaviors

- Projects page: `https://chatgpt.com/projects`
- Existing project rows: `[role="row"].group.EhAptG_selectableRow`
- New project buttons:
  - `button[aria-label="New project"]`
  - `button:has-text("New")`
- Project name input:
  - `input[name="projectName"]`
  - `#project-name`
- Create button:
  - `button:has-text("Create project")`

## Normalization rule

Normalize row text before matching names. The Projects page can append date text like `TodayToday` or month/day strings directly onto the project name.

## Failure notes

- Older sidebar-based helpers can fail on brittle click targets.
- Use the Projects page directly instead of relying on the old home/sidebar route.
- A stale persistent Chromium instance can lock the ChatGPT profile; kill it and retry once.
