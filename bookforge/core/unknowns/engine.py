"""Suggestions engine for Unknowns resolver."""

from __future__ import annotations

import re
from bookforge.core.unknowns.parser import BookContext


def _suggest_year(item: str, ctx: BookContext) -> list[str]:
    """Generate three plausible year suggestions for a Western setting."""
    decade_match = re.search(r"\b(18[5-9]\d|190\d)\b", ctx.raw)
    if decade_match:
        base = int(decade_match.group(1))
    else:
        base = 1880
    years = sorted({max(1860, base - 2), base, min(1899, base + 2)})
    return [str(y) for y in years]


def _suggest_appearance(item: str, ctx: BookContext) -> list[str]:
    """Suggest appearance descriptions appropriate for a Western antagonist."""
    name_m = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s appearance", item, re.IGNORECASE)
    name = name_m.group(1) if name_m else "The character"
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
