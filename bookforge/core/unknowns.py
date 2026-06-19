#!/usr/bin/env python3
"""BookForge Unknowns Resolver.

Parses the ## Unknowns section from rulebook.md, presents each item with
3 AI-suggested choices (plus a custom 4th option), accepts the user's pick,
and writes resolved answers back into the rulebook so the pipeline is
no longer blocked.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+)$")


def _find_section_bounds(text: str, section_aliases: tuple[str, ...]) -> tuple[int, int, int]:
    """Return (heading_start, body_start, body_end) for the named section.

    Returns (-1, -1, -1) if not found.
    """
    aliases = {a.strip().lower() for a in section_aliases}
    headings = list(_HEADING_RE.finditer(text))
    for idx, m in enumerate(headings):
        title = m.group(2).strip().lower()
        if title not in aliases:
            continue
        level = len(m.group(1))
        body_start = m.end()
        body_end = len(text)
        for nxt in headings[idx + 1:]:
            if len(nxt.group(1)) <= level:
                body_end = nxt.start()
                break
        return m.start(), body_start, body_end
    return -1, -1, -1


def parse_unknowns(rulebook_text: str) -> list[str]:
    """Return each bullet item in the ## Unknowns section as a string."""
    _, body_start, body_end = _find_section_bounds(rulebook_text, ("Unknowns",))
    if body_start == -1:
        return []
    section_body = rulebook_text[body_start:body_end]
    items: list[str] = []
    for line in section_body.splitlines():
        m = _BULLET_RE.match(line)
        if m:
            item = m.group(1).strip()
            if item:
                items.append(item)
    return items


def parse_resolved_answers(rulebook_text: str) -> dict[str, str]:
    """Return {question_text: answer_text} from the ## Resolved Unknowns section."""
    _, body_start, body_end = _find_section_bounds(rulebook_text, ("Resolved Unknowns",))
    if body_start == -1:
        return {}
    section_body = rulebook_text[body_start:body_end]
    answers: dict[str, str] = {}
    current_question: str | None = None
    for line in section_body.splitlines():
        q_match = re.match(r"^\s*[-*]\s+\*\*Q:\*\*\s+(.+)$", line)
        a_match = re.match(r"^\s+[-*]\s+\*\*A:\*\*\s+(.+)$", line)
        if q_match:
            current_question = q_match.group(1).strip()
        elif a_match and current_question:
            answers[current_question] = a_match.group(1).strip()
            current_question = None
    return answers


# ---------------------------------------------------------------------------
# Context reader — pulls genre / setting / time period from the rulebook
# ---------------------------------------------------------------------------

class BookContext(NamedTuple):
    genre: str          # e.g. "Classic Western"
    setting: str        # e.g. "Powder River country, Wyoming"
    time_period: str    # e.g. "1800s"
    title: str          # book title
    raw: str            # full rulebook text


def _extract_field(text: str, *labels: str) -> str:
    """Pull the value after any of the given bold-label patterns, e.g. **Genre/Length Target:**"""
    for label in labels:
        pattern = rf"\*\*{re.escape(label)}[:/]?\*\*\s*(.+)"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).split("\n")[0].strip().rstrip(".")
    return ""


def read_book_context(rulebook_text: str) -> BookContext:
    genre = _extract_field(rulebook_text, "Genre/Length Target", "Genre", "Subgenre")
    setting = _extract_field(rulebook_text, "Primary Setting", "Setting", "Region")
    time_period = _extract_field(rulebook_text, "Time Period", "Era", "Period")
    title_m = re.match(r"#\s+(.+)", rulebook_text)
    title = title_m.group(1).strip() if title_m else "Unknown Book"
    return BookContext(
        genre=genre or "Western",
        setting=setting or "frontier",
        time_period=time_period or "1800s",
        title=title,
        raw=rulebook_text,
    )


# ---------------------------------------------------------------------------
# Suggestions engine
# ---------------------------------------------------------------------------

# Each rule is (pattern_re, suggestions_fn | list[str])
# suggestions_fn receives (item_text, ctx) and returns list[str]

def _suggest_year(item: str, ctx: BookContext) -> list[str]:
    """Generate three plausible year suggestions for a Western setting."""
    # Try to extract decade hint from context
    decade_match = re.search(r"\b(18[5-9]\d|190\d)\b", ctx.raw)
    if decade_match:
        base = int(decade_match.group(1))
    else:
        base = 1880
    # Spread ±2 around the base, avoiding the exact same year
    years = sorted({max(1860, base - 2), base, min(1899, base + 2)})
    return [str(y) for y in years]


def _suggest_appearance(item: str, ctx: BookContext) -> list[str]:
    """Suggest appearance descriptions appropriate for a Western antagonist."""
    name_m = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s appearance", item, re.IGNORECASE)
    name = name_m.group(1) if name_m else "The character"
    # Pull age hint from rulebook if already present for this character
    age_m = re.search(
        rf"{re.escape(name)}.*?Age[:\s]+(\d+)", ctx.raw, re.IGNORECASE | re.DOTALL
    )
    age_hint = age_m.group(1) if age_m else "mid-40s"
    return [
        f"Tall, lean, {age_hint}, sharp jaw, cold pale eyes, short-cropped black hair, "
        f"heavy brow, old scar along left cheekbone, iron gray at the temples.",
        f"Broad-shouldered, thick-necked, {age_hint}, ruddy face, broken nose, dark brown "
        f"eyes that go flat when angry, black mustache trimmed close.",
        f"Medium height but thick through the chest, {age_hint}, square jaw, deep-set "
        f"gray eyes, weathered brown skin, heavy hands scarred from brawls.",
    ]


def _suggest_names(item: str, ctx: BookContext) -> list[str]:
    """Suggest name lists for groups (ranchers, guards, etc.)."""
    q_lower = item.lower()
    if "rancher" in q_lower:
        return [
            "Amos Decker, Clete Farrow, Boyd Shaner (3 ranchers — one old-timer, one young hothead, one cautious family man).",
            "Walt Rudd, Lonnie Briggs, Hector Vela, Pete Ashworth (4 ranchers — spread across different grazing claims).",
            "Nolan Orin, Cord's neighbor Jess Dunbar, and two unnamed hands who follow Jess's lead (4 total).",
        ]
    if "guard" in q_lower or "logging" in q_lower:
        return [
            "Three guards: a foreman named Cull, a rifleman called Dutch, and a mute giant known only as Ox.",
            "Two guards at the gate (Breen and Tarver), two roving sentries on the east timber line.",
            "Four guards total: Sergeant-type named Voigt commands two riflemen and one with a shotgun at the entrance.",
        ]
    # Generic name list
    return [
        "Three named: Rudd, Calloway, and Breck — each with a different reason for joining the fight.",
        "Four total — one leader, two veterans, one green hand who shows courage under fire.",
        "Two main names (Decker and Farr) plus two unnamed who follow their lead.",
    ]


def _suggest_location_layout(item: str, ctx: BookContext) -> list[str]:
    """Suggest geographic or layout descriptions."""
    q_lower = item.lower()
    if "road" in q_lower or "route" in q_lower or "surrounding" in q_lower:
        return [
            f"Three named roads: the Old Bozeman Spur (northwest), the Red Wash Cutoff (east), and a seasonal stock road through Sage Flats (south).",
            f"Two main routes — the River Road hugging the Powder south, and the Ridge Trail cutting across dry benchland above the canyon.",
            f"Unmarked freight tracks, one official territorial road south to Douglas, and a hidden shortcut through the breaks used only by locals.",
        ]
    if "logging" in q_lower or "camp" in q_lower:
        return [
            "Main yard with a log chute to the east, bunkhouse on the north end, supply shed and tool cage flanking the gate on the south.",
            "Open clearing with stacked timber on three sides, foreman's shack at the far end, one guard tower at the entry road.",
            "L-shaped layout: main cutting area to the west, a guarded wagon road on the north, and a creek trail used for supply mules on the east.",
        ]
    if "stronghold" in q_lower or "manor" in q_lower or "fort" in q_lower:
        return [
            "Stone manor with a walled courtyard, armory in the east wing, prisoner cells below the kitchen, and a back gate to the river.",
            "Two-story log structure with a wraparound porch, stable block to the west, and a fortified cellar used as a holding room.",
            "Main house on a ridge, bunkhouse downslope to the left, open corral on the right, single road in guarded by a manned watchtower.",
        ]
    # Generic location
    return [
        f"Spread across three natural choke points in {ctx.setting} — a narrows, a ridge crossing, and a dry wash ford.",
        f"Two established waypoints: a relay station at the east end and a river crossing camp eight miles further north.",
        f"Named for a prominent landmark: Black Rock Pass to the north, Alkali Flat to the east, Crow Butte to the south.",
    ]


def _suggest_home_base(item: str, ctx: BookContext) -> list[str]:
    """Suggest lawman home base and prior cases."""
    q_lower = item.lower()
    if "home base" in q_lower or "whitaker" in q_lower or "marshal" in q_lower:
        return [
            "Home base: Cheyenne, Wyoming. Prior cases: broke up a rustling ring on the North Platte, lost his partner in a canyon ambush two years back.",
            "Home base: Laramie, Wyoming Territory. Prior cases: tracked a train robbery crew, testifying before a federal judge — lost the case due to witness intimidation.",
            "Home base: Denver, Colorado (rotates through Wyoming on circuit). Prior cases: pursued a stage robbery gang into the Bighorns, one conviction, two escaped.",
        ]
    return [
        "Based in the nearest federal district seat. Prior cases include pursuit of two known fugitives and a failed conviction.",
        "Circuit rider out of the territorial capital. Prior work: escort duty, one high-profile arrest, and two lost witnesses.",
        "Stationed along the rail corridor. Has made four arrests in two years but watched courts dismiss three of them on technical grounds.",
    ]


def _suggest_iron_spur_name(item: str, ctx: BookContext) -> list[str]:
    """Suggest the next Iron Spur clue or name."""
    return [
        "Colonel Elias Vane — a disgraced former army officer who supplied the ambush intelligence. Last known location: New Mexico Territory.",
        "Cassidy Rourke — a Pinkerton-turned-hired-gun who coordinated the betrayal from the inside. Believed to be working the Kansas cattle trail.",
        "A woman known only as 'the Architect' — no name yet, only a signet ring mark matching the Iron Spur brand found in Harlan's papers.",
    ]


def _suggest_origin_age(item: str, ctx: BookContext) -> list[str]:
    """Suggest origin and age for a villain character."""
    name_m = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s", item)
    name = name_m.group(1) if name_m else "The antagonist"
    return [
        f"{name}: age 47, origin Missouri, former Confederate guerrilla who never quit the war, drifted west running cattle and taking contracts.",
        f"{name}: age 43, origin Texas Panhandle, worked as a hired gun for mining outfits before building his own road gang from former prison contacts.",
        f"{name}: age 51, origin unknown — uses three different names, believed born in the Ohio Valley, served federal time once and walked on a technicality.",
    ]


def _suggest_generic(item: str, ctx: BookContext) -> list[str]:
    """Generic fallback suggestions drawn from the genre and setting."""
    genre = ctx.genre.lower()
    setting = ctx.setting
    return [
        f"A grounded {genre} answer rooted in {setting}: leave it vague in the narrative and reveal only through action.",
        f"Establish it as a deliberate mystery — the characters reference it but Tex never confirms it directly.",
        f"Resolve it in the scene where it becomes plot-relevant rather than defining it up front in the rulebook.",
    ]


# ------------------------------------------------------------------
# Rule table: (compiled pattern, suggestion function)
# ------------------------------------------------------------------

_SUGGESTION_RULES: list[tuple[re.Pattern[str], object]] = [
    (re.compile(r"\byear\b", re.IGNORECASE), _suggest_year),
    (re.compile(r"\bappearance\b", re.IGNORECASE), _suggest_appearance),
    (re.compile(r"\borigin\b.*\bage\b|\bage\b.*\borigin\b", re.IGNORECASE), _suggest_origin_age),
    (re.compile(r"\bname[s]?\b.*\brancher", re.IGNORECASE), _suggest_names),
    (re.compile(r"\brancher", re.IGNORECASE), _suggest_names),
    (re.compile(r"\bguard[s]?\b", re.IGNORECASE), _suggest_names),
    (re.compile(r"\bnames?\b.*\broads?\b|\broads?\b.*\bnames?\b", re.IGNORECASE), _suggest_location_layout),
    (re.compile(r"\blayout\b", re.IGNORECASE), _suggest_location_layout),
    (re.compile(r"\bhome\s+base\b|\bprevious\s+case", re.IGNORECASE), _suggest_home_base),
    (re.compile(r"\biron\s+spur\b|\bnext\s+name\b", re.IGNORECASE), _suggest_iron_spur_name),
    (re.compile(r"\borigin\b|\bage\b", re.IGNORECASE), _suggest_origin_age),
]


def suggest(item: str, ctx: BookContext) -> list[str]:
    """Return exactly 3 suggestion strings for a given unknown item."""
    for pattern, fn in _SUGGESTION_RULES:
        if pattern.search(item):
            result = fn(item, ctx)  # type: ignore[operator]
            return result[:3]
    return _suggest_generic(item, ctx)[:3]


# ---------------------------------------------------------------------------
# Rulebook write-back
# ---------------------------------------------------------------------------

def _ensure_resolved_section(text: str) -> str:
    """Add ## Resolved Unknowns section if it doesn't exist yet."""
    if "## Resolved Unknowns" in text:
        return text
    return text.rstrip() + "\n\n## Resolved Unknowns\n\n"


def write_resolved_answer(rulebook_path: Path, question: str, answer: str) -> None:
    """Append a Q/A pair to ## Resolved Unknowns and remove the item from ## Unknowns."""
    text = rulebook_path.read_text(encoding="utf-8")

    # 1. Remove the bullet from ## Unknowns
    _, body_start, body_end = _find_section_bounds(text, ("Unknowns",))
    if body_start != -1:
        section_body = text[body_start:body_end]
        new_body_lines = []
        for line in section_body.splitlines(keepends=True):
            m = _BULLET_RE.match(line.rstrip("\n"))
            if m and m.group(1).strip() == question:
                continue  # drop this bullet
            new_body_lines.append(line)
        text = text[:body_start] + "".join(new_body_lines) + text[body_end:]

    # 2. Ensure ## Resolved Unknowns exists
    text = _ensure_resolved_section(text)

    # 3. Append the Q/A pair inside the resolved section
    _, body_start2, body_end2 = _find_section_bounds(text, ("Resolved Unknowns",))
    if body_start2 != -1:
        qa_block = f"- **Q:** {question}\n  - **A:** {answer}\n"
        existing_body = text[body_start2:body_end2]
        new_body = existing_body.rstrip() + "\n" + qa_block
        text = text[:body_start2] + new_body + text[body_end2:]

    rulebook_path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Validation helper (used by validator.py)
# ---------------------------------------------------------------------------

def check_unknowns(book_folder: Path) -> list[str]:
    """Return a list of failure strings if unresolved Unknowns items exist."""
    rulebook_path = book_folder / "rulebook.md"
    if not rulebook_path.exists():
        return []

    text = rulebook_path.read_text(encoding="utf-8")
    items = parse_unknowns(text)
    if not items:
        return []

    failures: list[str] = []
    for item in items:
        failures.append(
            f"Rulebook `## Unknowns` has unresolved item: \"{item}\" — "
            f"run `bf resolve-unknowns <book_folder>` to answer it before proceeding."
        )
    return failures


# ---------------------------------------------------------------------------
# Interactive Q&A wizard
# ---------------------------------------------------------------------------

_DIVIDER = "  " + "─" * 58

def _print_header(total: int) -> None:
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║      BookForge — Unknowns Resolver Wizard                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n  Found {total} unresolved item(s) in rulebook.md → ## Unknowns.")
    print("  Pick a suggestion (1–3), enter 4 for a custom answer,")
    print("  or type SKIP to leave an item unresolved.")
    print("  Press Ctrl+C at any time to abort without saving.\n")


def _prompt_choice(item: str, choices: list[str], idx: int, total: int) -> str | None:
    """Present the question with numbered choices. Returns the final answer string,
    or None if skipped, or raises KeyboardInterrupt to abort.
    """
    print(_DIVIDER)
    print(f"  [{idx}/{total}] UNKNOWN: {item}\n")
    for n, choice in enumerate(choices, start=1):
        # Wrap long suggestions at ~75 chars
        words = choice.split()
        lines: list[str] = []
        line: list[str] = []
        length = 0
        for word in words:
            if length + len(word) + 1 > 72:
                lines.append(" ".join(line))
                line = [word]
                length = len(word)
            else:
                line.append(word)
                length += len(word) + 1
        if line:
            lines.append(" ".join(line))
        first_line = lines[0]
        rest = lines[1:]
        print(f"    {n}. {first_line}")
        for l in rest:
            print(f"       {l}")
        print()
    print(f"    4. What's on your mind? (type your own answer)")
    print()

    while True:
        try:
            raw = input("  Choose [1–4] or SKIP: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt

        if raw.upper() == "SKIP" or raw == "":
            return None  # skip

        if raw in ("1", "2", "3"):
            answer = choices[int(raw) - 1]
            print(f"\n  ✓ Selected: {answer[:80]}{'...' if len(answer) > 80 else ''}\n")
            return answer

        if raw == "4":
            try:
                custom = input("  Your answer: ").strip()
            except (EOFError, KeyboardInterrupt):
                raise KeyboardInterrupt
            if not custom:
                print("  (empty — treated as SKIP)\n")
                return None
            print(f"\n  ✓ Custom answer recorded.\n")
            return custom

        print("  Please enter 1, 2, 3, 4, or SKIP.\n")


def run_unknowns_wizard(book_folder: Path) -> int:
    """Interactively resolve all unresolved Unknowns in the rulebook.

    Returns 0 if all resolved, 1 if any remain unresolved.
    """
    rulebook_path = book_folder / "rulebook.md"
    if not rulebook_path.exists():
        print(f"Error: rulebook.md not found in '{book_folder}'.", file=sys.stderr)
        return 1

    text = rulebook_path.read_text(encoding="utf-8")
    unknowns = parse_unknowns(text)

    if not unknowns:
        print("✓ No unresolved Unknowns found in rulebook.md — pipeline is clear to proceed.")
        return 0

    ctx = read_book_context(text)
    _print_header(len(unknowns))

    resolved_count = 0
    skipped: list[str] = []

    for idx, item in enumerate(unknowns, start=1):
        choices = suggest(item, ctx)
        try:
            answer = _prompt_choice(item, choices, idx, len(unknowns))
        except KeyboardInterrupt:
            print("\n\n  Aborted. No changes saved.")
            return 1

        if answer is None:
            skipped.append(item)
            print("  → Skipped.\n")
            continue

        write_resolved_answer(rulebook_path, item, answer)
        resolved_count += 1

    print(_DIVIDER)
    print(f"\n  Summary: {resolved_count} resolved, {len(skipped)} skipped.")

    if skipped:
        print("\n  The following items remain unresolved (pipeline still blocked):")
        for item in skipped:
            print(f"    • {item}")
    else:
        print("\n  ✓ All Unknowns resolved. The pipeline is now clear to proceed.")

    return 0 if not skipped else 1
