import re
from pathlib import Path

manuscript_path = Path("books/tex-cade/books-2/manuscript.md")
content = manuscript_path.read_text(encoding="utf-8")

# Let's find index of "Beat 2" or "## Beat" in the original content
original_lines = content.splitlines()
for idx, line in enumerate(original_lines):
    if "## Beat 2" in line:
        print(f"Original surrounding lines (around line {idx}):")
        for i in range(max(0, idx-3), min(len(original_lines), idx+5)):
            print(f"{i}: {original_lines[i]}")
        break

# Process
clean_content = re.sub(r"(?m)^## Beat.*$\n*", "", content)
clean_content = re.sub(r'([\"”])\s*—\s*', r'\1 ', clean_content)
clean_content = re.sub(r"\n{3,}", "\n\n", clean_content)

clean_lines = clean_content.splitlines()
# Let's find where the transition happened in clean_content
# We can search for the text near the transition
for idx, line in enumerate(clean_lines):
    if "Bowen's eyes went to the trail" in line:
        print("\nCleaned surrounding lines:")
        for i in range(max(0, idx-3), min(len(clean_lines), idx+5)):
            print(f"{i}: {clean_lines[i]}")
        break
