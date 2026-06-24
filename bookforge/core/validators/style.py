"""Style-related validation functions and constants."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Style patterns & constants
DEFAULT_SETTINGS: dict[str, Any] = {
    "operator_prose_guard": {
        "enabled": True,
        "mode": "advisory",          # "advisory" | "hard"
        "output_token_cap": 500,
        "operator_personas": ["extractor", "reviewer", "planner"],
        "prose_actions": ["draft", "draft_prose", "expand"],
    },
    "name_policy": {
        "banned_names": [],
        "allowed_names": [],
        "scope": "system_forward",
    },
    "style_review": {
        "enabled": True,
        "review_only": True,
        "max_summary_words_without_dialogue": 120,
        "analysis_terms": [
            "realized",
            "processed",
            "understood",
            "psychological",
            "emotional",
            "motif",
            "symbolism",
        ],
        "formal_dialogue_terms": [
            "traverse",
            "obscures",
            "therefore",
            "endeavor",
            "proceed",
            "will be",
            "shall",
            "ought",
            "cannot",
            "require",
            "indicate",
            "attempt",
            "sufficient",
            "furthermore",
            "consequently",
            "nevertheless",
        ],
        "time_jump_terms": [
            "hours later",
            "days later",
            "weeks later",
            "after some time",
        ],
        "warn_short_sentence_runs": True,
        "banned_terms": [
            "no clean answer",
            "tactical position",
            "leverage",
            "pressure point",
            "emotional cost",
            "control the ground",
            "move fast",
            "stay focused",
            "legalese",
            "cost center",
            "synergy",
            "bandwidth",
            "stakeholder",
            "deliverable",
            "action item",
            "team player",
            "circle back",
            "move the needle",
            "low-hanging fruit",
            "deep dive",
            "take offline",
            "game changer",
            "paradigm",
            "disruption",
        ],
    },
    "historical_terms": {
        "banned": [
            "cost center",
        ],
        "warn": [],
        "context_required": [
            "appeal",
            "civil judgment",
            "cooperation will be recorded",
            "custody",
            "exhibit",
            "foreclosure petition",
            "mortgage lien",
            "sequestration",
            "writ",
        ],
        "review_only": [
            "bank packet",
            "bond",
            "court",
            "hearing",
            "petition",
            "signature page",
            "warrant",
            "witness list",
        ],
    },
    "style_profiles": {
        "fallback_profile": "default",
        "year_buckets": [
            {
                "name": "frontier_1880s",
                "start": 1880,
                "end": 1899,
            },
            {
                "name": "frontier_transition_1900s",
                "start": 1900,
                "end": 1912,
            },
        ],
        "profiles": {
            "default": {
                "voice": {
                    "banned_slang": ["y'all", "howdy", "partner", "reckon", "drawl"],
                },
            },
            "frontier_1880s": {
                "voice": {
                    "banned_slang": ["y'all", "howdy", "partner", "reckon", "drawl"],
                },
            },
            "frontier_transition_1900s": {
                "voice": {
                    "banned_slang": ["y'all", "drawl", "reckon"],
                },
            },
        },
    },
    "plot_mode_review": {
        "enabled": True,
        "review_only": True,
        "legal_procedure_threshold": 6,
        "ban_markers": [
            "no courtroom",
            "no courtrooms",
            "no trial",
            "no trial scene",
            "no legal-procedure",
            "no legal procedure",
        ],
        "legal_procedure_terms": [
            "appeal",
            "bond",
            "civil judgment",
            "court",
            "courtroom",
            "custody",
            "exhibit",
            "foreclosure",
            "hearing",
            "judge",
            "legal",
            "lien",
            "mortgage",
            "petition",
            "sequestration",
            "trial",
            "warrant",
            "witness list",
            "writ",
        ],
    },
}

BANNED_AI_ECHO_WORDS = [
    "absolutely",
    "completely",
    "relentless",
    "massive",
    "sharp",
    "heavy",
    "pure",
    "extremely",
    "perfectly",
]

MODERN_OR_CLINICAL_WORDS = [
    "velocity",
    "fraction",
    "trajectory",
    "impact",
    "visible",
    "resolving",
    "cost center",
    "synergy",
    "bandwidth",
    "stakeholder",
    "deliverable",
    "action item",
    "team player",
    "circle back",
    "move the needle",
    "low-hanging fruit",
    "deep dive",
    "take offline",
    "game changer",
    "paradigm",
    "disruption",
    "explosion",
    "debris",
    "shrapnel",
    "artillery",
    "impact zone",
]

INTERNAL_MONOLOGUE_PHRASES = [
    "he felt", "he realized", "he thought", "he knew", "he wondered",
    "he believed", "he hoped", "he feared", "he decided", "he suspected",
    "she felt", "she realized", "she thought", "she knew", "she wondered",
    "she believed", "she hoped", "she feared", "she decided", "she suspected",
    "they felt", "they realized", "they thought", "they knew", "they wondered",
]

# Compatibility vocabulary used by the loop's broad style scan. Precise draft
# validation is handled by forbidden_length_language().
FORBIDDEN_LENGTH_LANGUAGE = ["word count", "words", "quota", "target"]

FORBIDDEN_CONFLICT_PATTERNS = {
    "water rights": r"\bwater\s+rights?\b",
    "syndicate": r"\bsyndicates?\b",
    "land grab": r"\bland\s*grabs?\b",
    "business scheme": r"\bbusiness\s+schemes?\b",
    "organized corruption": r"\borganized\s+corruption\b",
    "property dispute": r"\bproperty\s+disputes?\b",
    "business conspiracy": r"\bbusiness\s+conspirac(?:y|ies)\b",
    "syndicate-style": r"\bsyndicate-style\b",
    "voss": r"\bvoss\b",
    "rafe": r"\brafe\b",
    "silas": r"\bsilas\b",
}

PROJECT_RULE_BANNED_NAME_LABELS = {"voss", "rafe", "silas"}

ING_OPENER_RE = re.compile(r"(?m)^([A-Z][A-Za-z]{2,}ing)\b[\s,]")
ING_OPENER_EXCLUSIONS = {
    "during", "bring", "ring", "sing", "thing", "spring",
    "morning", "evening", "nothing", "something", "everything", "anything",
    "king", "wing", "sling", "string", "cling", "fling", "sting", "swing", "wring",
    "lightning", "awning", "ceiling", "lining", "sterling", "cunning", "darling",
    "sibling", "sapling", "farthing", "inkling", "shilling", "herring", "pudding"
}

DIALOGUE_TAG_RE = re.compile(
    r'"[^"]*"\s*(?:—\s*)?(?:[A-Z][A-Za-z\'-]*\s+)?'
    r"(said|asked|shouted|whispered|cried|replied|exclaimed|called|muttered|grumbled|demanded)\b"
    r'|'
    r"\b(said|asked|shouted|whispered|cried|replied|exclaimed|called|muttered|grumbled|demanded)\s*,\s*\"[^\"]*\"",
    re.IGNORECASE,
)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
PRONOUN_FIXED = frozenset({"he", "she", "they", "it"})
PRONOUN_LOOP_MIN_RUN = 3

STOPWORDS = {
    "about", "after", "again", "against", "all", "and", "any", "are", "because", "been", "before",
    "being", "between", "both", "but", "came", "come", "did", "down", "each", "few", "for", "from",
    "had", "has", "have", "her", "here", "him", "his", "how", "into", "its", "just", "like", "many",
    "more", "most", "off", "once", "only", "other", "our", "out", "over", "same", "she", "should",
    "some", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "those", "through", "too", "under", "until", "upon", "very", "was", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _read_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _deep_merge_settings(base: dict[str, Any], override: Any) -> dict[str, Any]:
    if not isinstance(base, dict):
        return _as_dict(override)
    override_map = _as_dict(override)
    merged: dict[str, Any] = {}
    for key, value in base.items():
        if isinstance(value, dict):
            merged[key] = _deep_merge_settings(value, override_map.get(key))
        elif key in override_map:
            merged[key] = override_map[key]
        else:
            merged[key] = value
    for key, value in override_map.items():
        if key not in merged:
            merged[key] = value
    return merged


_TIME_PERIOD_FIELD_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*{0,2})?"
    r"(time period|era|period)"
    r"(?:\*{0,2})?\s*[:/\-]?\s*(.+)$"
)
_YEAR_RE = re.compile(r"\b(?:19[0-9]{2}|18[0-9]{2})\b")
_DECADE_RE = re.compile(r"\b((?:18|19)\d)0s\b", re.IGNORECASE)


def _extract_time_period_text(rulebook_text: str) -> str:
    try:
        match = re.search(r"\*\*(Time Period|Era|Period)[:/]?\*\*\s*(.+)", rulebook_text, re.IGNORECASE)
        if match:
            return match.group(2).split("\n")[0].strip()
    except Exception:
        pass

    for line in rulebook_text.splitlines():
        match = _TIME_PERIOD_FIELD_RE.match(line)
        if match:
            return match.group(2).split("\n")[0].strip()
    return ""


def _extract_year_from_text(value: str) -> int | None:
    if not value:
        return None

    normalized = value.strip()
    match = _YEAR_RE.search(normalized)
    if match:
        return _read_int(match.group(0))

    decade_match = _DECADE_RE.search(normalized)
    if decade_match:
        return _read_int(f"{decade_match.group(1)}0")
    return None


def _extract_book_year_from_rulebook(rulebook_text: str) -> int | None:
    return _extract_year_from_text(_extract_time_period_text(rulebook_text))


def _extract_book_year_from_source_text(source_text: str) -> int | None:
    match = re.search(r"(?i)Period:\s*.*?(\d{4})", source_text)
    if match:
        year = _read_int(match.group(1))
        if year is not None:
            return year
    return _extract_year_from_text(source_text)


def _extract_book_year_from_book_folder(project_root: Path) -> int | None:
    try:
        rulebook_path = project_root / "rulebook.md"
        if rulebook_path.exists():
            rulebook_text = rulebook_path.read_text(encoding="utf-8")
            year = _extract_book_year_from_rulebook(rulebook_text)
            if year is not None:
                return year
    except OSError:
        pass

    try:
        from bookforge.core.scanner import source_path

        source = source_path(project_root)
        if source and source.exists():
            source_text = source.read_text(encoding="utf-8")
            year = _extract_book_year_from_source_text(source_text)
            if year is not None:
                return year
    except Exception:
        pass

    return None


def resolve_style_profile(
    settings_start: Path | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Resolve era profile + merged style/historical/voice settings."""
    from bookforge.core.validators.format import find_project_root, load_project_settings

    settings = load_project_settings(settings_start)
    project_root = find_project_root(settings_start)

    style_profiles = _as_dict(settings.get("style_profiles"))
    year_buckets = style_profiles.get("year_buckets")
    if not isinstance(year_buckets, list):
        year_buckets = []
    profiles = _as_dict(style_profiles.get("profiles"))
    fallback_profile = "default"
    configured_fallback = style_profiles.get("fallback_profile")
    if isinstance(configured_fallback, str) and configured_fallback.strip():
        fallback_profile = configured_fallback.strip()
    if fallback_profile not in profiles:
        fallback_profile = "default"

    book_year = _extract_book_year_from_book_folder(project_root)
    profile_name = fallback_profile
    if isinstance(book_year, int):
        for bucket in year_buckets:
            if not isinstance(bucket, dict):
                continue
            name = bucket.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            start = _read_int(bucket.get("start"))
            end = _read_int(bucket.get("end"))
            if start is None:
                continue
            if end is None:
                end = start
            if start > end:
                start, end = end, start
            if start <= book_year <= end:
                profile_name = name.strip()
                break

    if profile_name not in profiles:
        profile_name = "default"

    base_style = _as_dict(settings.get("style_review"))
    base_historical = _as_dict(settings.get("historical_terms"))
    profile_settings = _as_dict(profiles.get(profile_name))
    resolved_style_review = _deep_merge_settings(base_style, profile_settings.get("style_review"))
    resolved_historical_terms = _deep_merge_settings(base_historical, profile_settings.get("historical_terms"))
    voice_settings = _as_dict(profile_settings.get("voice"))

    return (
        profile_name,
        resolved_style_review,
        resolved_historical_terms,
        voice_settings,
    )


def contains_any(text: str, words: list[str], case_sensitive: bool = False) -> list[str]:
    flags = 0 if case_sensitive else re.IGNORECASE
    matched = []
    for word in words:
        if re.search(rf"\b{re.escape(word)}\b", text, flags):
            matched.append(word)
    return matched


def check_ing_openers(text: str) -> list[str]:
    samples: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"([A-Z][A-Za-z]{2,}ing)\b[\s,]", stripped)
        if match and match.group(1).lower() not in ING_OPENER_EXCLUSIONS:
            samples.append(stripped[:100])
            if len(samples) >= 5:
                break
    return samples


def extract_proper_names(text: str, word_limit: int = 200) -> set[str]:
    words = text.split()[:word_limit]
    names: set[str] = set()
    for word in words:
        clean = re.sub(r"[^A-Za-z]", "", word)
        if clean and clean[0].isupper() and len(clean) > 3 and clean.lower() not in STOPWORDS:
            names.add(clean.lower())
    return names


def check_pronoun_loops(text: str) -> list[str]:
    sentences = SENTENCE_SPLIT_RE.split(text)
    proper_names = extract_proper_names(text)
    watch_tokens = PRONOUN_FIXED | proper_names
    findings: list[str] = []
    run_token: str | None = None
    run_count = 0
    for sentence in sentences:
        stripped = sentence.strip()
        if not stripped:
            run_token = None
            run_count = 0
            continue
        first_word_match = re.match(r"([A-Za-z]+)", stripped)
        if not first_word_match:
            run_token = None
            run_count = 0
            continue
        token = first_word_match.group(1).lower()
        if token not in watch_tokens:
            run_token = None
            run_count = 0
            continue
        if token == run_token:
            run_count += 1
        else:
            run_token = token
            run_count = 1
        if run_count == PRONOUN_LOOP_MIN_RUN:
            findings.append(
                f"{run_count}+ consecutive sentences starting with '{first_word_match.group(1)}'"
            )
    return findings


def dialogue_tags(text: str) -> list[str]:
    found: set[str] = set()
    for match in DIALOGUE_TAG_RE.finditer(text):
        tag = match.group(1) or match.group(2)
        if tag:
            found.add(tag.lower())
    return sorted(found)


def check_em_dash_anchors(text: str) -> list[str]:
    warnings: list[str] = []
    for line_num, line in enumerate(text.splitlines(), 1):
        if '"' in line:
            if '--' in line:
                warnings.append(f"Line {line_num}: Use em-dash `—` instead of double-hyphen `--`")
                continue
            for match in re.finditer(r'"[^"]*"\s*—\s*\S?', line):
                if not re.search(r'"[^"]*"\s—\s\S', match.group(0)):
                    warnings.append(
                        f"Line {line_num}: Incorrect em-dash anchor spacing. Use `\"Dialogue.\" — Action`."
                    )
    return warnings


def _normalize_sentence(sentence: str) -> str:
    words = re.findall(r"\b[A-Za-z']+\b", sentence.lower())
    return " ".join(words)


def check_repeated_sentence_duplicates(text: str) -> list[str]:
    """Find likely copy-paste sentence duplicates without flagging tiny refrains."""
    findings: list[str] = []
    seen: dict[str, str] = {}
    for sentence in SENTENCE_SPLIT_RE.split(text.strip()):
        clean = sentence.strip()
        normalized = _normalize_sentence(clean)
        if len(normalized.split()) < 5:
            continue
        if normalized in seen:
            findings.append(f"Repeated sentence likely copy-paste: {seen[normalized][:120]}")
            if len(findings) >= 5:
                break
            continue
        seen[normalized] = clean
    return findings


def forbidden_length_language(text: str) -> list[str]:
    findings: list[str] = []
    patterns = {
        "word count": r"\bword counts?\b",
        "quota": r"\bquotas?\b",
        "target": r"\b(?:target|minimum|maximum)\s+(?:word|words|length)\b",
        "fixed words": r"\b\d[\d,]*\s+words?\b",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(label)
    return findings


def _configured_banned_name_patterns(settings: dict[str, Any]) -> dict[str, str]:
    name_policy = settings.get("name_policy", {})
    banned_names = name_policy.get("banned_names", [])
    allowed_names = name_policy.get("allowed_names", [])
    if not isinstance(banned_names, list):
        banned_names = []
    if not isinstance(allowed_names, list):
        allowed_names = []

    allowed = {str(name).strip().lower() for name in allowed_names if str(name).strip()}
    patterns: dict[str, str] = {}
    for raw_name in banned_names:
        name = str(raw_name).strip().lower()
        if not name:
            continue
        if name in allowed and name not in PROJECT_RULE_BANNED_NAME_LABELS:
            continue
        patterns[name] = rf"\b{re.escape(name)}\b"
    return patterns


def check_forbidden_conflicts(text: str, settings_start: Path | None = None) -> list[str]:
    from bookforge.core.validators.format import load_project_settings
    findings: list[str] = []
    text_lower = text.lower()
    settings = load_project_settings(settings_start)

    patterns = {
        **FORBIDDEN_CONFLICT_PATTERNS,
        **_configured_banned_name_patterns(settings),
    }

    for label, pattern in patterns.items():
        if re.search(pattern, text_lower):
            if label == "voss":
                findings.append("Banned character/setting name 'voss' found.")
            elif label in _configured_banned_name_patterns(settings):
                findings.append(f"Configured banned name '{label}' found.")
            else:
                findings.append(f"Forbidden conflict theme/term '{label}' found in draft.")
    return findings


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _term_hits(text_lower: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    for term in terms:
        pattern = rf"\b{re.escape(term)}\b" if re.search(r"\w", term) else re.escape(term)
        if re.search(pattern, text_lower):
            hits.append(term)
    return sorted(set(hits))


def check_plot_mode_risk(text: str, book_folder: Path | None = None) -> list[str]:
    """Warn when a banned plot mode appears to dominate the draft."""
    from bookforge.core.validators.format import load_project_settings

    settings = load_project_settings(book_folder)
    review_settings = settings.get("plot_mode_review", {})
    if not isinstance(review_settings, dict) or not review_settings.get("enabled", True):
        return []

    if book_folder is None:
        return []
    rulebook_path = Path(book_folder) / "rulebook.md"
    if not rulebook_path.exists():
        return []

    rulebook_text = rulebook_path.read_text(encoding="utf-8").lower()
    ban_markers = _as_string_list(review_settings.get("ban_markers"))
    if not any(marker in rulebook_text for marker in ban_markers):
        return []

    terms = _as_string_list(review_settings.get("legal_procedure_terms"))
    text_lower = text.lower()
    hits = _term_hits(text_lower, terms)
    threshold = review_settings.get("legal_procedure_threshold", 6)
    if not isinstance(threshold, int) or threshold < 1:
        threshold = 6
    if len(hits) < threshold:
        return []

    return [
        "Draft appears to lean into legal-procedure plot mode despite rulebook guardrails; "
        f"review before rewriting. Terms: {', '.join(hits[:10])}."
    ]
def check_similes_and_metaphors(text: str) -> list[str]:
    # Strip double quoted dialogue to check narrative only
    narrative = re.sub(r'"[^"]*"', '', text)
    sentences = SENTENCE_SPLIT_RE.split(narrative)
    
    simile_pat = re.compile(
        r'\b(as\s+if|as\s+though|like\s+(?:a|an|the|my|his|her|its|our|their|your|some|any|wet|old|dry|cold|hot|dark|bright|thin|thick|sharp|hard|soft|wild|dead|living|slow|fast|heavy|light|\w+))\b',
        re.IGNORECASE
    )
    
    non_similes = {
        "like to", "like it", "like this", "like that", "like these", "like those",
        "like so", "like me", "like us", "like you", "like him", "like her", "like them",
        "would like", "should like", "could like", "does like", "did like", "do like",
        "nothing like", "anything like", "something like", "not like to", "don't like",
        "feel like", "feels like", "felt like", "seemed like", "seems like", "seem like",
        "look like", "looks like", "looked like"
    }
    
    findings = []
    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        
        matches = simile_pat.finditer(sentence_clean)
        for match in matches:
            matched_str = match.group(1).lower()
            
            # Check if it is a known non-simile pattern
            is_non_simile = False
            if matched_str.startswith("like"):
                like_start = match.start()
                sentence_lower = sentence_clean.lower()
                
                # Check for preceding non-simile verbs/phrases ending in 'like'
                pre_text = sentence_lower[:like_start + 4]  # includes 'like'
                for non_simile in non_similes:
                    if non_simile.endswith("like"):
                        if pre_text.endswith(non_simile):
                            is_non_simile = True
                            break
                            
                # Check for succeeding non-simile phrases starting with 'like'
                if not is_non_simile:
                    post_text = sentence_lower[like_start:]
                    for non_simile in non_similes:
                        if non_simile.startswith("like"):
                            if post_text.startswith(non_simile):
                                next_char_idx = len(non_simile)
                                if next_char_idx >= len(post_text) or not post_text[next_char_idx].isalnum():
                                    is_non_simile = True
                                    break
            
            if not is_non_simile:
                snippet = sentence_clean[:80] + "..." if len(sentence_clean) > 80 else sentence_clean
                findings.append(f"Simile/Metaphor detected in narrative: '{snippet}' (found '{match.group(1)}')")
                break # Warn once per sentence
    return findings


def check_personification_of_objects(text: str) -> list[str]:
    # Strip double quoted dialogue to check narrative only
    narrative = re.sub(r'"[^"]*"', '', text)
    sentences = SENTENCE_SPLIT_RE.split(narrative)
    
    # Nouns representing inanimate objects or abstract concepts
    inanimate_nouns = (
        r"land|wind|dust|night|sun|sky|shadow|shadows|darkness|fire|smoke|stone|rock|paper|wood|wagon|wheel|carriage|train|"
        r"saddle|scabbard|bullet|lead|iron|steel|leather|rope|water|river|creek|mud|snow|trail|road|arroyo|valley|ridge|cliff|"
        r"mountain|hill|slope|wonder|fear|pain|silence|danger|memory|memories|thought|time|hour|hours|minute|minutes|day|"
        r"days|week|weeks|season|seasons|year|years|truth|lie|lies|voice|sound|word|words|name|names|blood|bloodstain|heat|"
        r"cold|winter|summer|spring|autumn|fall|weather|colt|rifle|gun|revolver|pistol|carbine|winchester|"
        r"habit|name|paper|room|door|window|fence|gate|wall|floor|ground|dirt|clay|sand|grass|brush|mesquite|cedar|pine|"
        r"oak|elm|cottonwood|sky|cloud|storm|rain|frost|ice|wind|breeze|gust|heat|cold|chill|warmth|"
        r"distance|miles|mile|league|day|night|dawn|dusk|twilight|sunrise|sunset|moon|stars|constellation"
    )
    
    # Verbs representing human-like action, communication, or mental states
    agency_verbs = (
        r"speak|speaks|spoke|speaking|talk|talks|talked|talking|whisper|whispers|whispered|whispering|tell|tells|told|telling|"
        r"say|says|said|saying|want|wants|wanted|wanting|wish|wishes|wished|wishing|hope|hopes|hoped|hoping|know|knows|knew|"
        r"knowing|think|thinks|thought|thinking|believe|believes|believed|believing|wonder|wonders|wondered|wondering|waste|"
        r"wastes|wasted|wasting|watch|watches|watched|watching|creep|creeps|crept|creeping|breathe|breathes|breathed|breathing|"
        r"listen|listens|listened|listening|stare|stares|stared|staring|gaze|gazes|gazed|gazing|move|moves|moved|moving|stretch|"
        r"stretches|stretched|stretching|chase|chases|chased|chasing|"
        r"put|puts|putting|hold|holds|held|holding|reach|reaches|reached|reaching|"
        r"cry|cries|cried|crying|laugh|laughs|laughed|laughing|weep|weeps|wept|weeping|"
        r"call|calls|called|calling|scream|screams|screamed|screaming|"
        r"bite|bites|bit|biting|scratch|scratches|scratched|scratching|"
        r"fight|fights|fought|fighting|kill|kills|killed|killing|"
        r"run|runs|ran|running|walk|walks|walked|walking|climb|climbs|climbed|climbing|"
        r"wait|waits|waited|waiting|sleep|sleeps|slept|sleeping|dream|dreams|dreamed|dreaming"
    )
    
    personification_pat = re.compile(
        rf"\b({inanimate_nouns})\b(?:\s+(?:did\s+not|had|was|were|could|would|should|will|can|might)\b)?(?:\s+[a-z]+ly\b)?\s+\b({agency_verbs})\b",
        re.IGNORECASE
    )
    
    # Look for gun/rifle equated to warning/curse/etc.
    metaphor_pat = re.compile(
        rf"\b(colt|rifle|gun|revolver|pistol|carbine|winchester)\b(?:\s+(?:was|were|is|are)\b)?\s+(?:a|an)\s+\b(curse|warning|blessing|promise|threat|enemy|friend|companion|partner)\b",
        re.IGNORECASE
    )
    
    findings = []
    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        
        match = personification_pat.search(sentence_clean)
        if match:
            snippet = sentence_clean[:80] + "..." if len(sentence_clean) > 80 else sentence_clean
            findings.append(
                f"Personification of inanimate object/concept '{match.group(1)}' with action '{match.group(2)}': '{snippet}'"
            )
            continue
            
        metaphor_match = metaphor_pat.search(sentence_clean)
        if metaphor_match:
            snippet = sentence_clean[:80] + "..." if len(sentence_clean) > 80 else sentence_clean
            findings.append(
                f"Metaphorical/figurative description of weapon '{metaphor_match.group(1)}' as '{metaphor_match.group(2)}': '{snippet}'"
            )
            
    return findings


def check_abstract_internalization(text: str) -> list[str]:
    # Strip double quoted dialogue to check narrative only
    narrative = re.sub(r'"[^"]*"', '', text)
    sentences = SENTENCE_SPLIT_RE.split(narrative)
    
    # Check for pronoun/character name followed by internalization verb
    subjects = r"he|she|they|jed|branton|harlan|tex|creed|lask|eleanor"
    internal_verbs = (
        r"knew|known|know|believed|believe|wondered|wonder|resolved|resolve|decided|decide|"
        r"expected|expect|doubted|doubt|suspected|suspect|predicted|predict|"
        r"sensed|sense|remembered|remember|forgot|forgotten|forget|wished|wish|hoped|hope|"
        r"recalled|recall|imagined|imagine|feared|fear"
    )
    
    internal_pat = re.compile(
        rf"\b({subjects})\b"
        rf"(?:\s+(?:had|was|were|did|could|would|should|will|can|might)\b)?"
        rf"(?:\s+(?:not|never)\b)?"
        rf"(?:\s+[a-z]+ly\b)?"
        rf"\s+\b({internal_verbs})\b",
        re.IGNORECASE
    )
    
    findings = []
    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        
        match = internal_pat.search(sentence_clean)
        if match:
            snippet = sentence_clean[:80] + "..." if len(sentence_clean) > 80 else sentence_clean
            findings.append(
                f"Abstract internalization / thought-summary detected for '{match.group(1)}' with '{match.group(2)}': '{snippet}'"
            )
    return findings


def check_style_review_signals(text: str, settings_start: Path | None = None) -> list[str]:
    try:
        _, style_settings, historical_terms, _ = resolve_style_profile(settings_start)
    except Exception:
        from bookforge.core.validators.format import load_project_settings
        settings = load_project_settings(settings_start)
        style_settings = settings.get("style_review", {})
        historical_terms = _as_dict(settings.get("historical_terms"))

    style_settings = _as_dict(style_settings)
    if not isinstance(style_settings, dict) or not style_settings.get("enabled", True):
        return []
    if not isinstance(historical_terms, dict):
        historical_terms = {}
    historical_terms = _as_dict(historical_terms)

    findings: list[str] = []
    max_summary_words = style_settings.get("max_summary_words_without_dialogue", 120)
    if not isinstance(max_summary_words, int) or max_summary_words < 1:
        max_summary_words = 120

    for paragraph in re.split(r"\n\s*\n", text.strip()):
        words = re.findall(r"\b[A-Za-z']+\b", paragraph)
        if len(words) >= max_summary_words and '"' not in paragraph:
            findings.append(
                f"Long narrative-summary stretch without dialogue ({len(words)} words); review whether an active exchange or physical beat is needed."
            )
            break

    text_lower = text.lower()
    analysis_terms = [term for term in _as_string_list(style_settings.get("analysis_terms")) if re.search(rf"\b{re.escape(term)}\b", text_lower)]
    if analysis_terms:
        findings.append(
            "Behavior-analysis language appears in draft; review for action/dialogue replacement: "
            + ", ".join(sorted(set(analysis_terms))[:8])
            + "."
        )

    formal_terms = _as_string_list(style_settings.get("formal_dialogue_terms"))
    dialogue_segments = re.findall(r'"([^"]+)"', text)
    formal_hits: set[str] = set()
    for segment in dialogue_segments:
        segment_lower = segment.lower()
        for term in formal_terms:
            if re.search(rf"\b{re.escape(term)}\b", segment_lower):
                formal_hits.add(term)
    if formal_hits:
        findings.append(
            "Formal dialogue terms appear inside quoted speech; review for rugged Western phrasing: "
            + ", ".join(sorted(formal_hits)[:8])
            + "."
        )

    time_jump_terms = [term for term in _as_string_list(style_settings.get("time_jump_terms")) if term in text_lower]
    if time_jump_terms:
        findings.append(
            "Abrupt time-jump wording appears; review whether the transition needs trail labor, scouting, camp movement, or consequence: "
            + ", ".join(sorted(set(time_jump_terms))[:8])
            + "."
        )

    banned_terms = [term for term in _as_string_list(style_settings.get("banned_terms")) if re.search(rf"\b{re.escape(term)}\b", text_lower)]
    if banned_terms:
        findings.append(
            "Forbidden modern or legalese/clinical terms appear in draft; replace with period-accurate phrasing: "
            + ", ".join(sorted(set(banned_terms))[:8])
            + "."
        )

    if isinstance(historical_terms, dict):
        severity_labels = (
            ("banned", "Banned historical/style terms"),
            ("warn", "Warn historical/style terms"),
            ("context_required", "Context-required historical/style terms"),
            ("review_only", "Review-only historical/style terms"),
        )
        for key, label in severity_labels:
            hits = _term_hits(text_lower, _as_string_list(historical_terms.get(key)))
            if hits:
                findings.append(f"{label} found; verify timeline and genre fit: {', '.join(hits[:8])}.")

    if style_settings.get("warn_short_sentence_runs", False):
        sentences = SENTENCE_SPLIT_RE.split(text)
        short_run = 0
        short_sentences_detected = []
        for sentence in sentences:
            clean_sentence = sentence.strip()
            if not clean_sentence:
                continue
            words = re.findall(r"\b[A-Za-z']+\b", clean_sentence)
            if len(words) > 0 and len(words) < 5:
                short_run += 1
                if short_run >= 3:
                    short_sentences_detected.append(clean_sentence)
            else:
                short_run = 0

        if short_sentences_detected:
            findings.append(
                "Consecutive short sentence fragments detected (rhythm feels too modern/clipped); review and combine for classic cadence: "
                + "; ".join(short_sentences_detected[:3])
                + "..."
            )

    findings.extend(check_similes_and_metaphors(text))
    findings.extend(check_personification_of_objects(text))
    findings.extend(check_abstract_internalization(text))
    findings.extend(check_duplicated_actions(text))
    findings.extend(check_impossible_frontier_actions(text))
    findings.extend(check_ai_staccato_drama(text))
    findings.extend(check_rule_of_three(text))
    findings.extend(check_em_dash_overuse(text))

    return findings


def check_duplicated_actions(text: str) -> list[str]:
    """Detect same action described twice in close proximity (different wording)."""
    findings: list[str] = []
    paragraphs = re.split(r"\n\s*\n", text.strip())

    action_verbs = (
        r"dragged|drag|pull|pulled|push|pushed|lift|lifted|raise|raised|set|placed|"
        r"checked|examine|examined|looked|stared|gazed|watched|"
        r"fired|shot|aimed|raised|lowered|drew|reached|"
        r"rode|mounted|dismounted|tied|untied|saddled|unsaddled|"
        r"cut|tied|broke|fixed|mended|repaired"
    )

    seen_actions: list[tuple[str, int]] = []
    for i, para in enumerate(paragraphs):
        para_clean = para.strip()
        if not para_clean or len(para_clean.split()) < 10:
            continue
        sentences = SENTENCE_SPLIT_RE.split(para_clean)
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue
            words_list = re.findall(r"\b[A-Za-z']+\b", sentence_clean)
            if len(words_list) < 5:
                continue
            match = re.search(rf"\b({action_verbs})\b", sentence_clean, re.IGNORECASE)
            if not match:
                continue
            verb = match.group(1).lower()
            normalized = _normalize_sentence(sentence_clean)
            for prev_normalized, prev_idx in seen_actions:
                if prev_idx == i:
                    continue
                overlap = len(set(normalized.split()) & set(prev_normalized.split()))
                total = len(set(normalized.split()) | set(prev_normalized.split()))
                if total > 0 and overlap / total > 0.5 and abs(i - prev_idx) <= 5:
                    snippet = sentence_clean[:120]
                    findings.append(
                        f"Possible duplicated action (similar content, different words): '{snippet}'"
                    )
                    if len(findings) >= 5:
                        return findings
            seen_actions.append((normalized, i))

    return findings


def check_impossible_frontier_actions(text: str) -> list[str]:
    """Flag physically impossible or highly implausible frontier actions."""
    findings: list[str] = []
    text_lower = text.lower()

    impossible_patterns = [
        (r" wagon[s]?\s+.*(?:on|onto|aboard)\s+(?:the\s+)?(?:flat\s*boat|ferry|barge).*(?:moving|drift|current|away)",
         "Wagon driven onto a moving flatboat/ferry — physically implausible."),
        (r" bullet[s]?\s+.*(?:explod|burst|shatter).*(?:snow|ice|frost|ground)",
         "Bullet exploding on snow/ice impact — lead bullets do not detonate."),
        (r"(?:spot|found|saw|noticed)\s+.*(?:sliver|splinter|toothpick|splinter).*(?:mud|dirt|churned|track)",
         "Tiny object spotted in churned mud — implausible tracking detail."),
        (r"(?:faster|outrun|beat).*(?:map|charted|know(?:n)?)\s+.*(?:route|path|trail)",
         "Character outpacing map-holders on unknown ground — implausible."),
    ]

    for pattern, message in impossible_patterns:
        if re.search(pattern, text_lower):
            findings.append(f"Frontier realism warning: {message}")

    return findings


def check_ai_staccato_drama(text: str) -> list[str]:
    """Detect 3+ consecutive short declarative fragments manufacturing drama."""
    findings: list[str] = []
    sentences = SENTENCE_SPLIT_RE.split(text)
    short_fragments: list[str] = []

    for sentence in sentences:
        clean = sentence.strip()
        if not clean:
            continue
        words = re.findall(r"\b[A-Za-z']+\b", clean)
        if 1 <= len(words) <= 6 and clean.rstrip().endswith("."):
            short_fragments.append(clean)
        else:
            if len(short_fragments) >= 3:
                snippet = "; ".join(short_fragments[:4])
                findings.append(
                    f"AI staccato drama: {len(short_fragments)} consecutive short fragments: '{snippet}'"
                )
                if len(findings) >= 3:
                    return findings
            short_fragments = []

    if len(short_fragments) >= 3:
        snippet = "; ".join(short_fragments[:4])
        findings.append(
            f"AI staccato drama: {len(short_fragments)} consecutive short fragments: '{snippet}'"
        )

    return findings


def check_rule_of_three(text: str) -> list[str]:
    """Detect forced groups of three items in close proximity."""
    findings: list[str] = []
    lines = text.splitlines()

    comma_triple_re = re.compile(
        r"(\b[A-Z][a-z]+(?:\s+\w+){0,3}),\s+(\b[A-Z][a-z]+(?:\s+\w+){0,3}),\s+and\s+(\b[A-Z][a-z]+(?:\s+\w+){0,3})\b"
    )

    for line_num, line in enumerate(lines, 1):
        if '"' in line:
            continue
        matches = list(comma_triple_re.finditer(line))
        if len(matches) >= 2:
            findings.append(
                f"Line {line_num}: Multiple rule-of-three groupings in same sentence — may feel forced."
            )
            if len(findings) >= 3:
                return findings

    return findings


def check_em_dash_overuse(text: str) -> list[str]:
    """Flag paragraphs with 3+ em dashes."""
    findings: list[str] = []
    paragraphs = re.split(r"\n\s*\n", text.strip())

    for i, para in enumerate(paragraphs):
        em_dash_count = para.count("—")
        if em_dash_count >= 3:
            snippet = para[:100]
            findings.append(
                f"Paragraph {i + 1}: {em_dash_count} em dashes — consider reducing for cleaner prose: '{snippet}...'"
            )
            if len(findings) >= 3:
                return findings

    return findings
