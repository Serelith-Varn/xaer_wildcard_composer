import json
import os
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from server import PromptServer
    from aiohttp import web
    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False

DEFAULT_WILDCARD_DIR = str(
    Path(__file__).resolve().parent.parent
    / "ComfyUI-Impact-Pack"
    / "wildcards"
    / "xaer_thalassor"
)

CONFIG_FILENAME = "node_config.json"
CHARACTER_MASTER_FILE = "xaer_characters.txt"

CATEGORIES = ["prefix", "character", "action", "location", "suffix", "unassigned"]
PROTECTED_BULK_CATEGORIES = {"prefix", "location", "suffix"}

NAMED_CHAR_CONFLICT_FILES = {
    "head.txt",
    "eyecolor.txt",
}

FIELD_LABEL_PREFIX_RE = re.compile(
    r"^(?:Colors?|Characters?|Prefix|Suffix|Locations?|Actions?|Heads?|Ears?|"
    r"Eyeware|Eyewear|Eye\s*color|Eyes?|Nose|Mouth|Expressions?|Naughty|"
    r"Neck|Shoulders?|Torso|Back|Waist(?:\s*&\s*Midriff)?|"
    r"Arms?(?:\s*\(?Full\)?)?|Upper\s*Arms?|Forearms?|Wrists?|"
    r"Hands?(?:\s*&\s*Fingers)?|Pelvis|Thighs?|Knees?|Legs?|Calves?|Ankles?|"
    r"Feet(?:\s*&\s*Toes)?|Archetypes?|Armors?|Outfits?)\s*:\s*",
    re.IGNORECASE,
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "2.5.1",
    "character_master_file": CHARACTER_MASTER_FILE,
    "excluded_files": [
        "armors.txt",
        "xaer_actions.txt",
        "xaer_char_archetype_clean.txt",
        "xaer_eyecolor.txt",
        "xaer_female_bottomwear.txt",
        "xaer_female_character01.txt",
        "xaer_female_character02.txt",
    ],
    "default_categories": {
        "prefix": [
            "pony_glob_prefix.txt",
            "zimage_glob_prefix.txt",
            "minimaxh3_glob_prefix.txt",
            "prefix.txt",
            "xaer_prefix.txt",
        ],
        "character": [
            "head.txt",
            "hairstyle.txt",
            "xaer_hairstyle.txt",
            "Ears.txt",
            "eyeware.txt",
            "eyecolor.txt",
            "Nose.txt",
            "Mouth.txt",
            "expression.txt",
            "Neck.txt",
            "Shoulders.txt",
            "Torso.txt",
            "Back.txt",
            "Waist & Midriff.txt",
            "Arms (Full).txt",
            "Upper Arms.txt",
            "Forearms.txt",
            "Wrists.txt",
            "Hands & Fingers.txt",
            "Pelvis.txt",
            "Thighs.txt",
            "Knees.txt",
            "Legs.txt",
            "Calves.txt",
            "Ankles.txt",
            "Feet & Toes.txt",
            "xaer_outfit.txt",
            "xaer_clothes.txt",
            "xaer_female_topwear.txt",
            "xaer_regalia.txt",
            "naughty.txt",
            "xaer_naughty.txt",
        ],
        "action": [
            "xaer_solo_actions.txt",
            "xaer_pair_actions.txt",
        ],
        "location": [
            "xaer_locations.txt",
        ],
        "suffix": [
            "pony_glob_suffix.txt",
            "zimage_glob_suffix.txt",
            "minimaxh3_glob_suffix.txt",
            "suffix.txt",
            "xaer_suffix.txt",
        ],
    },
    "default_enabled": [
        "expression.txt",
        "eyecolor.txt",
        "hairstyle.txt",
        "xaer_solo_actions.txt",
        "xaer_locations.txt",
    ],
    "node_layouts": {},
}

XAER_GOTHIC_NSFW_TAGS = (
    "detailed, beautiful, gothic fantasy aesthetic, photo, photorealistic, "
    "detailed skin texture, pores, beautiful dark fantasy illustration, "
    "dramatic chiaroscuro lighting, perfect face, only women, 8k resolution, NSFW"
)

PONY_QUALITY_PRESETS = [
    "None",
    "Custom (Use Text Input)",
    f"score_9, score_8_up, score_7_up, {XAER_GOTHIC_NSFW_TAGS}",
    "score_9, score_8_up, score_7_up, source_anime",
    "score_9, score_8_up, score_7_up, source_realistic",
]

ZIMAGE_STYLE_PRESETS = [
    "None",
    "Custom (Use Text Input)",
    XAER_GOTHIC_NSFW_TAGS,
    "Cinematic medium shot, dramatic chiaroscuro rim lighting, 35mm film grain, ultra-detailed textures",
    "Editorial dark fantasy portrait, moody volumetric fog, sharp focus, rich natural lighting",
]

MINIMAX_CAMERA_PRESETS = [
    "None",
    "Custom (Use Text Input)",
    "Slow cinematic dolly-in with subtle handheld micro-movement, dramatic chiaroscuro rim lighting, shallow depth of field.",
    "Smooth lateral tracking shot following the subjects across the scene, steady 35mm lens, atmospheric depth.",
    "Slow low-angle crane rise revealing full posture and environment, moody volumetric lighting.",
    "Static locked-off medium wide shot with subtle environmental motion, natural filmic grain.",
]


def load_or_init_config(wildcard_dir: str) -> Dict[str, Any]:
    dir_path = Path(wildcard_dir)
    config_path = dir_path / CONFIG_FILENAME
    if not dir_path.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))

    if not config_path.exists():
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        except OSError:
            pass
        return json.loads(json.dumps(DEFAULT_CONFIG))

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        merged = json.loads(json.dumps(DEFAULT_CONFIG))
        merged.update(loaded)
        excl = set(merged.get("excluded_files", []))
        excl.update(DEFAULT_CONFIG["excluded_files"])
        merged["excluded_files"] = sorted(excl)
        return merged
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(wildcard_dir: str, config: Dict[str, Any]) -> bool:
    dir_path = Path(wildcard_dir)
    if not dir_path.exists():
        return False
    config_path = dir_path / CONFIG_FILENAME
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def is_file_compatible_with_node(filename: str, target_node: str, config: Dict[str, Any]) -> bool:
    lower = filename.lower()
    if not lower.endswith(".txt"):
        return False
    if filename == config.get("character_master_file", CHARACTER_MASTER_FILE):
        return False
    if filename in config.get("excluded_files", []):
        return False

    if lower.startswith("pony_"):
        return target_node == "pony"
    if lower.startswith("zimage_"):
        return target_node == "zimage"
    if lower.startswith("minimaxh3_"):
        return target_node == "minimaxh3"
    return True


def infer_initial_category(filename: str, config: Dict[str, Any]) -> str:
    lower = filename.lower()
    if lower in ("simple_colors.txt", "xaer_simple_colors.txt"):
        return "unassigned"

    stripped = re.sub(r"^(pony|zimage|minimaxh3|all)_", "", lower)
    if stripped.startswith(("prefix", "glob_prefix")):
        return "prefix"
    if stripped.startswith(("suffix", "glob_suffix")):
        return "suffix"
    if stripped.startswith(("loc_", "location", "glob_loc")):
        return "location"
    if stripped.startswith(("act_", "action")):
        return "action"

    default_cats = config.get("default_categories", {})
    for cat in ["prefix", "character", "action", "location", "suffix"]:
        if filename in default_cats.get(cat, []):
            return cat
    return "unassigned"


def build_node_layout(wildcard_dir: str, target_node: str) -> Dict[str, List[Dict[str, Any]]]:
    config = load_or_init_config(wildcard_dir)
    dir_path = Path(wildcard_dir)
    layout: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CATEGORIES}
    if not dir_path.is_dir():
        return layout

    available_files = [
        f
        for f in sorted(os.listdir(dir_path), key=lambda s: s.lower())
        if (dir_path / f).is_file() and is_file_compatible_with_node(f, target_node, config)
    ]
    available_set = set(available_files)

    saved_node_layout = config.get("node_layouts", {}).get(target_node)
    placed_files = set()

    if isinstance(saved_node_layout, dict):
        for cat in CATEGORIES:
            for item in saved_node_layout.get(cat, []):
                fname = item.get("file", "")
                if fname in available_set and fname not in placed_files:
                    layout[cat].append({
                        "file": fname,
                        "enabled": bool(item.get("enabled", False)),
                    })
                    placed_files.add(fname)

    default_enabled = set(config.get("default_enabled", []))
    cat_order_map: Dict[str, List[str]] = config.get("default_categories", {})

    remaining = [f for f in available_files if f not in placed_files]
    priority_index: Dict[str, int] = {}
    idx_counter = 0
    for cat in ["prefix", "character", "action", "location", "suffix"]:
        for fname in cat_order_map.get(cat, []):
            priority_index[fname] = idx_counter
            idx_counter += 1

    remaining.sort(key=lambda f: (priority_index.get(f, 99999), f.lower()))

    for fname in remaining:
        cat = infer_initial_category(fname, config)
        layout[cat].append({
            "file": fname,
            "enabled": fname in default_enabled,
        })

    return layout


def read_wildcard_lines(filepath: Path) -> List[str]:
    if not filepath.is_file():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            seen = set()
            unique_lines: List[str] = []
            for raw in f.readlines():
                cleaned = raw.strip().lstrip(",").strip()
                if cleaned and not cleaned.startswith("#") and cleaned not in seen:
                    seen.add(cleaned)
                    unique_lines.append(cleaned)
            return unique_lines
    except OSError:
        return []


def resolve_dynamic_braces(
    text: str,
    rng: random.Random,
    dir_path: Optional[Path] = None,
    file_cache: Optional[Dict[str, List[str]]] = None,
) -> str:
    """
    Recursively resolves {wildcard_file} references (e.g., {simple_colors}),
    {opt1|opt2|opt3} and (opt1|opt2|opt3) choice blocks, and {tag:1.35} weights.
    """
    brace_pattern = re.compile(r"\{([^{}]*)\}")
    paren_choice_pattern = re.compile(r"\(([^()|]+\|[^()]+)\)")
    current = text

    for _ in range(30):
        match = brace_pattern.search(current)
        if match:
            inner = match.group(1).strip()
            if "|" in inner:
                chosen = rng.choice(inner.split("|"))
            elif dir_path is not None and not re.search(r":\d+(?:\.\d+)?$", inner):
                fname = inner if inner.lower().endswith(".txt") else f"{inner}.txt"
                if file_cache is not None and fname not in file_cache:
                    file_cache[fname] = read_wildcard_lines(dir_path / fname)
                lines = (
                    file_cache.get(fname, [])
                    if file_cache is not None
                    else read_wildcard_lines(dir_path / fname)
                )
                chosen = rng.choice(lines) if lines else inner
            else:
                chosen = inner
            current = current[: match.start()] + chosen + current[match.end() :]
            continue

        p_match = paren_choice_pattern.search(current)
        if p_match:
            chosen = rng.choice(p_match.group(1).split("|"))
            current = current[: p_match.start()] + chosen + current[p_match.end() :]
            continue

        break

    return current


def sanitize_line(
    raw_line: str,
    target_node: str,
    rng: Optional[random.Random] = None,
    is_armor_file: bool = False,
    is_location_file: bool = False,
    dir_path: Optional[Path] = None,
    file_cache: Optional[Dict[str, List[str]]] = None,
) -> str:
    line = raw_line.strip().lstrip(",").strip()
    if not line or line.startswith("#") or line.startswith("//"):
        return ""

    if rng is not None and (("{" in line and "}" in line) or ("|" in line and "(" in line)):
        line = resolve_dynamic_braces(line, rng, dir_path=dir_path, file_cache=file_cache)

    if is_armor_file or "Elements:" in line:
        if "Elements:" in line:
            line = line.split("Elements:", 1)[1].strip()
        line = re.sub(r"^Xaer Name:\s*[^|]+\|\s*", "", line).strip()

    if is_location_file and ":" in line:
        prefix_title, rest = line.split(":", 1)
        if len(prefix_title.split()) <= 6 and rest.strip():
            line = rest.strip()

    line = FIELD_LABEL_PREFIX_RE.sub("", line).strip()

    # Strip any "2::" or "5::" prefixes anywhere in the line (even glued after ")")
    line = re.sub(r"(?<![:\d.])\d+(?:\.\d+)?::", "", line).strip()
    # Fix incomplete trailing prepositions before weight colons, e.g. "of :1.15)" -> ":1.15)"
    line = re.sub(r"\bof\s*:(\d+(?:\.\d+)?)", r":\1", line)

    def _unwrap_parens(match: re.Match) -> str:
        inner = match.group(1).strip()
        if target_node == "pony" and re.search(r":\d+(\.\d+)?$", inner):
            return f"({inner})"
        return inner

    line = re.sub(r"\(([^()]+)\)", _unwrap_parens, line)
    line = re.sub(r"\s*,\s*,+", ", ", line)
    line = line.strip(" ,.;")
    return re.sub(r"\s{2,}", " ", line).strip()


def load_character_roster(wildcard_dir: str) -> Tuple[List[str], Dict[str, str]]:
    config = load_or_init_config(wildcard_dir)
    master_name = config.get("character_master_file", CHARACTER_MASTER_FILE)
    filepath = Path(wildcard_dir) / master_name
    lines = read_wildcard_lines(filepath)

    options = ["Random (Unique)", "None"]
    roster_map: Dict[str, str] = {}

    for line in lines:
        if line.lower().startswith("archetype:"):
            parts = line.split(",", 1)
            label = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else label
        elif " from " in line:
            label = line.split(" from ", 1)[0].strip()
            desc = line
        else:
            label = line.split(",", 1)[0].strip()
            desc = line

        if label in roster_map:
            suffix_num = 2
            while f"{label} ({suffix_num})" in roster_map:
                suffix_num += 1
            label = f"{label} ({suffix_num})"

        options.append(label)
        roster_map[label] = desc

    return options, roster_map


def resolve_preset_or_custom(preset_value: str, custom_value: str) -> str:
    p_clean = "" if str(preset_value).strip().startswith(("{", "[")) else str(preset_value).strip()
    c_clean = "" if str(custom_value).strip().startswith(("{", "[")) else str(custom_value).strip()

    if p_clean in ("", "None", "Custom (Use Text Input)"):
        return c_clean
    if c_clean:
        return f"{p_clean.rstrip(', ')}, {c_clean}"
    return p_clean


class _BaseXaerCategoryComposer:
    TARGET_NODE: str = ""
    MAX_CHARACTERS: int = 6
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt", "debug_breakdown")
    OUTPUT_NODE = True
    FUNCTION = "compose_prompt"
    CATEGORY = "Xaer'Thalassor/Prompting"

    @classmethod
    def _base_required_inputs(cls) -> Dict[str, Any]:
        char_options, _ = load_character_roster(DEFAULT_WILDCARD_DIR)
        default_layout = build_node_layout(DEFAULT_WILDCARD_DIR, cls.TARGET_NODE)
        req: Dict[str, Any] = {
            "wildcard_dir": ("STRING", {"default": DEFAULT_WILDCARD_DIR, "multiline": False}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            "character_count": ("INT", {"default": 1, "min": 1, "max": cls.MAX_CHARACTERS, "step": 1}),
        }
        for i in range(1, cls.MAX_CHARACTERS + 1):
            req[f"character_{i}"] = (char_options, {"default": "Random (Unique)"})

        req.update({
            "prevent_named_char_collisions": ("BOOLEAN", {"default": True}),
            "action_scope": (["per_character", "global"], {"default": "per_character"}),
            "wildcard_bulk_override": (
                [
                    "Use Individual Toggles",
                    "All On (Except Prefix/Location/Suffix)",
                    "All Off (Except Prefix/Location/Suffix)",
                ],
                {"default": "Use Individual Toggles"},
            ),
            "category_layout_json": (
                "STRING",
                {
                    "default": json.dumps(default_layout),
                    "multiline": True,
                },
            ),
        })
        return req

    def _parse_layout(
        self,
        wildcard_dir: str,
        category_layout_json: str,
        wildcard_bulk_override: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        fallback = build_node_layout(wildcard_dir, self.TARGET_NODE)
        result: Dict[str, List[Dict[str, Any]]] = fallback

        if category_layout_json and category_layout_json.strip():
            try:
                parsed = json.loads(category_layout_json)
                if isinstance(parsed, dict):
                    result = {c: [] for c in CATEGORIES}
                    for cat in CATEGORIES:
                        for entry in parsed.get(cat, []):
                            if isinstance(entry, dict) and "file" in entry:
                                result[cat].append({
                                    "file": str(entry["file"]),
                                    "enabled": bool(entry.get("enabled", False)),
                                })
            except json.JSONDecodeError:
                result = fallback

        if wildcard_bulk_override != "Use Individual Toggles":
            force_state = wildcard_bulk_override == "All On (Except Prefix/Location/Suffix)"
            for cat in CATEGORIES:
                if cat in PROTECTED_BULK_CATEGORIES or cat == "unassigned":
                    continue
                for entry in result.get(cat, []):
                    entry["enabled"] = force_state

        return result

    def _sample_category_once(
        self,
        rng: random.Random,
        dir_path: Path,
        entries: List[Dict[str, Any]],
        file_cache: Dict[str, List[str]],
        skip_files: Optional[set] = None,
    ) -> List[Tuple[str, str]]:
        rolled: List[Tuple[str, str]] = []
        for item in entries:
            if not item.get("enabled"):
                continue
            fname = item["file"]
            if skip_files and fname.lower() in skip_files:
                continue
            if fname not in file_cache:
                file_cache[fname] = read_wildcard_lines(dir_path / fname)
            lines = file_cache[fname]
            if not lines:
                continue
            raw_choice = rng.choice(lines)
            cleaned = sanitize_line(
                raw_choice,
                self.TARGET_NODE,
                rng=rng,
                is_armor_file=(fname.lower() == "armors.txt"),
                is_location_file=("location" in fname.lower()),
                dir_path=dir_path,
                file_cache=file_cache,
            )
            if cleaned:
                rolled.append((fname, cleaned))
        return rolled

    def _execute_rolls(
        self,
        wildcard_dir: str,
        seed: int,
        character_count: int,
        char_selections: List[str],
        prevent_named_char_collisions: bool,
        action_scope: str,
        wildcard_bulk_override: str,
        category_layout_json: str,
    ) -> Dict[str, Any]:
        character_count = max(1, min(self.MAX_CHARACTERS, int(character_count)))
        rng = random.Random(seed)
        dir_path = Path(wildcard_dir)
        layout = self._parse_layout(wildcard_dir, category_layout_json, wildcard_bulk_override)
        file_cache: Dict[str, List[str]] = {}

        _, roster_map = load_character_roster(wildcard_dir)
        all_names = list(roster_map.keys())
        used_names = set()

        active_selections = char_selections[:character_count]
        for sel in active_selections:
            if sel not in ("Random (Unique)", "None") and sel in roster_map:
                used_names.add(sel)

        resolved_characters: List[Dict[str, Any]] = []
        for idx in range(character_count):
            sel = active_selections[idx] if idx < len(active_selections) else "Random (Unique)"
            chosen_name = ""
            chosen_base_desc = ""

            if sel == "None":
                chosen_name = "None"
            elif sel != "Random (Unique)" and sel in roster_map:
                chosen_name = sel
                chosen_base_desc = sanitize_line(
                    roster_map[sel], self.TARGET_NODE, rng=rng, dir_path=dir_path, file_cache=file_cache
                )
            else:
                pool = [n for n in all_names if n not in used_names]
                if not pool:
                    pool = all_names
                if pool:
                    picked = rng.choice(pool)
                    used_names.add(picked)
                    chosen_name = picked
                    chosen_base_desc = sanitize_line(
                        roster_map[picked], self.TARGET_NODE, rng=rng, dir_path=dir_path, file_cache=file_cache
                    )

            is_named_character = (
                chosen_name not in ("", "None")
                and not chosen_name.lower().startswith("archetype:")
            )
            skip_set = NAMED_CHAR_CONFLICT_FILES if (prevent_named_char_collisions and is_named_character) else None

            char_traits = self._sample_category_once(
                rng, dir_path, layout.get("character", []), file_cache, skip_files=skip_set
            )
            char_actions: List[Tuple[str, str]] = []
            if action_scope == "per_character":
                char_actions = self._sample_category_once(
                    rng, dir_path, layout.get("action", []), file_cache
                )

            resolved_characters.append({
                "slot": idx + 1,
                "name": chosen_name,
                "base_desc": chosen_base_desc,
                "traits": char_traits,
                "actions": char_actions,
            })

        prefix_rolls = self._sample_category_once(rng, dir_path, layout.get("prefix", []), file_cache)
        global_action_rolls: List[Tuple[str, str]] = []
        if action_scope == "global":
            global_action_rolls = self._sample_category_once(
                rng, dir_path, layout.get("action", []), file_cache
            )
        location_rolls = self._sample_category_once(rng, dir_path, layout.get("location", []), file_cache)
        suffix_rolls = self._sample_category_once(rng, dir_path, layout.get("suffix", []), file_cache)

        return {
            "character_count": character_count,
            "prefix": prefix_rolls,
            "characters": resolved_characters,
            "global_actions": global_action_rolls,
            "location": location_rolls,
            "suffix": suffix_rolls,
        }

    @staticmethod
    def _dedupe_tags(parts: List[str]) -> List[str]:
        seen = set()
        cleaned: List[str] = []
        for chunk in parts:
            for tag in chunk.split(","):
                t = tag.strip()
                if not t:
                    continue
                key = t.lower()
                if key not in seen:
                    seen.add(key)
                    cleaned.append(t)
        return cleaned

    @staticmethod
    def _format_debug(model_label: str, seed: int, rolls: Dict[str, Any]) -> str:
        out = [f"=== {model_label} | Seed: {seed} | Characters: {rolls['character_count']} ==="]
        if rolls["prefix"]:
            out.append("\n[PREFIX]")
            for f, v in rolls["prefix"]:
                out.append(f"  - {f}: {v}")

        for c in rolls["characters"]:
            out.append(f"\n[CHARACTER {c['slot']}: {c['name']}]")
            if c["base_desc"]:
                out.append(f"  - Base Roster: {c['base_desc']}")
            for f, v in c["traits"]:
                out.append(f"  - {f}: {v}")
            for f, v in c["actions"]:
                out.append(f"  - [Action] {f}: {v}")

        if rolls["global_actions"]:
            out.append("\n[GLOBAL ACTION]")
            for f, v in rolls["global_actions"]:
                out.append(f"  - {f}: {v}")

        if rolls["location"]:
            out.append("\n[LOCATION]")
            for f, v in rolls["location"]:
                out.append(f"  - {f}: {v}")

        if rolls["suffix"]:
            out.append("\n[SUFFIX]")
            for f, v in rolls["suffix"]:
                out.append(f"  - {f}: {v}")

        return "\n".join(out)


class XaerPonyPromptComposer(_BaseXaerCategoryComposer):
    TARGET_NODE = "pony"
    MAX_CHARACTERS = 3

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        req = cls._base_required_inputs()
        req.update({
            "quality_preset": (PONY_QUALITY_PRESETS, {"default": "None"}),
            "custom_quality_tags": ("STRING", {"default": "", "multiline": True}),
            "auto_girl_count_tag": ("BOOLEAN", {"default": True}),
            "use_break_separator": ("BOOLEAN", {"default": True}),
        })
        return {"required": req}

    def _build_outputs(self, **kwargs: Any) -> Tuple[str, str]:
        char_count = max(1, min(self.MAX_CHARACTERS, int(kwargs.get("character_count", 1))))
        rolls = self._execute_rolls(
            kwargs["wildcard_dir"],
            int(kwargs["seed"]),
            char_count,
            [kwargs.get(f"character_{i}", "Random (Unique)") for i in range(1, self.MAX_CHARACTERS + 1)],
            bool(kwargs.get("prevent_named_char_collisions", True)),
            kwargs.get("action_scope", "per_character"),
            kwargs.get("wildcard_bulk_override", "Use Individual Toggles"),
            kwargs.get("category_layout_json", ""),
        )

        auto_girl_count_tag = bool(kwargs.get("auto_girl_count_tag", True))
        use_break_separator = bool(kwargs.get("use_break_separator", True))

        prefix_wildcard_values = [v for _, v in rolls["prefix"]]
        q_tags = resolve_preset_or_custom(
            kwargs.get("quality_preset", "None"),
            kwargs.get("custom_quality_tags", ""),
        )

        # 1. Guarantee score_9, score_8_up, score_7_up is ALWAYS first in Pony XL
        score_tokens: List[str] = []
        remaining_q_tags: List[str] = []
        solo_conflict_re = re.compile(r"^(?:solo|1girl|1person)$", re.IGNORECASE)

        for raw_chunk in ([q_tags] if q_tags else []) + prefix_wildcard_values:
            for tag in raw_chunk.split(","):
                t = tag.strip()
                if not t:
                    continue
                if re.match(r"^score_\d+(?:_up)?$", t, re.IGNORECASE):
                    score_tokens.append(t)
                elif char_count > 1 and solo_conflict_re.match(t):
                    continue
                else:
                    remaining_q_tags.append(t)

        if not score_tokens:
            score_tokens = ["score_9", "score_8_up", "score_7_up"]

        # 2. Auto-generate weighted count + multi-subject framing right after score tags
        count_tokens: List[str] = []
        if auto_girl_count_tag:
            if char_count == 1:
                count_tokens.extend(["1girl", "solo"])
            elif char_count == 2:
                count_tokens.extend(["(2girls:1.25)", "multiple girls", "two women", "wide shot"])
            else:
                count_tokens.extend([f"({char_count}girls:1.25)", "multiple girls", "three women", "wide shot"])

        prefix_parts = self._dedupe_tags(score_tokens + count_tokens + remaining_q_tags)

        # 3. Character blocks separated by BREAK (always enforced for 2+ characters)
        char_blocks: List[str] = []
        for c in rolls["characters"]:
            c_tags: List[str] = []
            if c["base_desc"]:
                c_tags.append(c["base_desc"])
            c_tags.extend(v for _, v in c["traits"])
            c_tags.extend(v for _, v in c["actions"])
            if c_tags:
                char_blocks.append(", ".join(c_tags))

        # 4. Global tail (Actions, Location, Suffix) isolated with BREAK
        tail_parts: List[str] = []
        tail_parts.extend(v for _, v in rolls["global_actions"])
        tail_parts.extend(v for _, v in rolls["location"])
        tail_parts.extend(v for _, v in rolls["suffix"])
        if char_count > 1:
            tail_parts = [
                t for t in self._dedupe_tags(tail_parts) if not solo_conflict_re.match(t)
            ]
        else:
            tail_parts = self._dedupe_tags(tail_parts)

        use_breaks = use_break_separator or (char_count > 1)
        segments: List[str] = []
        if prefix_parts:
            segments.append(", ".join(prefix_parts))
        if char_blocks:
            if use_breaks and len(char_blocks) > 1:
                segments.append(" BREAK ".join(char_blocks))
            else:
                segments.append(", ".join(char_blocks))

        if tail_parts:
            tail_str = ", ".join(tail_parts)
            if segments:
                full_prompt = ", ".join(segments) + f" BREAK {tail_str}"
            else:
                full_prompt = tail_str
        else:
            full_prompt = ", ".join(segments)

        debug_log = self._format_debug("Pony XL", int(kwargs["seed"]), rolls)
        return full_prompt, debug_log

    def compose_prompt(self, **kwargs: Any) -> Dict[str, Any]:
        full_prompt, debug_log = self._build_outputs(**kwargs)
        return {"ui": {"preview_text": [full_prompt]}, "result": (full_prompt, debug_log)}


class XaerZImagePromptComposer(_BaseXaerCategoryComposer):
    TARGET_NODE = "zimage"
    MAX_CHARACTERS = 6

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        req = cls._base_required_inputs()
        req.update({
            "style_preset": (ZIMAGE_STYLE_PRESETS, {"default": "None"}),
            "custom_style_prefix": ("STRING", {"default": "", "multiline": True}),
        })
        return {"required": req}

    def _build_outputs(self, **kwargs: Any) -> Tuple[str, str]:
        char_count = max(1, min(self.MAX_CHARACTERS, int(kwargs.get("character_count", 1))))
        rolls = self._execute_rolls(
            kwargs["wildcard_dir"],
            int(kwargs["seed"]),
            char_count,
            [kwargs.get(f"character_{i}", "Random (Unique)") for i in range(1, self.MAX_CHARACTERS + 1)],
            bool(kwargs.get("prevent_named_char_collisions", True)),
            kwargs.get("action_scope", "per_character"),
            kwargs.get("wildcard_bulk_override", "Use Individual Toggles"),
            kwargs.get("category_layout_json", ""),
        )

        sections: List[str] = []
        lead = resolve_preset_or_custom(
            kwargs.get("style_preset", "None"),
            kwargs.get("custom_style_prefix", ""),
        )
        if lead:
            lead_clean = sanitize_line(lead, self.TARGET_NODE)
            if lead_clean:
                sections.append(lead_clean.rstrip(".") + ".")

        if rolls["prefix"]:
            sections.append(", ".join(v for _, v in rolls["prefix"]) + ".")

        for c in rolls["characters"]:
            c_parts: List[str] = []
            if c["base_desc"]:
                c_parts.append(c["base_desc"])
            c_parts.extend(v for _, v in c["traits"])
            c_parts.extend(v for _, v in c["actions"])
            if c_parts:
                label = "Subject" if char_count == 1 else f"Character {c['slot']}"
                sections.append(f"{label}: {', '.join(c_parts)}.")

        if rolls["global_actions"]:
            sections.append(f"Action: {', '.join(v for _, v in rolls['global_actions'])}.")

        if rolls["location"]:
            sections.append(f"Setting: {', '.join(v for _, v in rolls['location'])}.")

        if rolls["suffix"]:
            sections.append(", ".join(v for _, v in rolls["suffix"]) + ".")

        full_prompt = " ".join(sections)
        debug_log = self._format_debug("Z-Image Turbo", int(kwargs["seed"]), rolls)
        return full_prompt, debug_log

    def compose_prompt(self, **kwargs: Any) -> Dict[str, Any]:
        full_prompt, debug_log = self._build_outputs(**kwargs)
        return {"ui": {"preview_text": [full_prompt]}, "result": (full_prompt, debug_log)}


class XaerMiniMaxH3PromptComposer(_BaseXaerCategoryComposer):
    TARGET_NODE = "minimaxh3"
    MAX_CHARACTERS = 6

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        req = cls._base_required_inputs()
        req.update({
            "camera_preset": (MINIMAX_CAMERA_PRESETS, {"default": "None"}),
            "custom_camera_direction": ("STRING", {"default": "", "multiline": True}),
        })
        return {"required": req}

    def _build_outputs(self, **kwargs: Any) -> Tuple[str, str]:
        char_count = max(1, min(self.MAX_CHARACTERS, int(kwargs.get("character_count", 1))))
        rolls = self._execute_rolls(
            kwargs["wildcard_dir"],
            int(kwargs["seed"]),
            char_count,
            [kwargs.get(f"character_{i}", "Random (Unique)") for i in range(1, self.MAX_CHARACTERS + 1)],
            bool(kwargs.get("prevent_named_char_collisions", True)),
            kwargs.get("action_scope", "per_character"),
            kwargs.get("wildcard_bulk_override", "Use Individual Toggles"),
            kwargs.get("category_layout_json", ""),
        )

        blocks: List[str] = []

        if rolls["prefix"]:
            blocks.append("[Visual Style & Framing]\n" + ", ".join(v for _, v in rolls["prefix"]) + ".")

        for c in rolls["characters"]:
            c_parts: List[str] = []
            if c["base_desc"]:
                c_parts.append(c["base_desc"])
            c_parts.extend(v for _, v in c["traits"])
            c_parts.extend(v for _, v in c["actions"])
            if c_parts:
                blocks.append(f"[Subject {c['slot']}]\n{', '.join(c_parts)}.")

        if rolls["global_actions"]:
            blocks.append("[Scene Action]\n" + ", ".join(v for _, v in rolls["global_actions"]) + ".")

        if rolls["location"]:
            blocks.append("[Environment & Atmosphere]\n" + ", ".join(v for _, v in rolls["location"]) + ".")

        cam_parts: List[str] = []
        cam_preset_str = resolve_preset_or_custom(
            kwargs.get("camera_preset", "None"),
            kwargs.get("custom_camera_direction", ""),
        )
        if cam_preset_str:
            cam_parts.append(cam_preset_str.rstrip("."))
        cam_parts.extend(v for _, v in rolls["suffix"])
        if cam_parts:
            blocks.append("[Camera & Cinematography]\n" + ". ".join(cam_parts) + ".")

        full_prompt = "\n\n".join(blocks)
        debug_log = self._format_debug("MiniMax H3", int(kwargs["seed"]), rolls)
        return full_prompt, debug_log

    def compose_prompt(self, **kwargs: Any) -> Dict[str, Any]:
        full_prompt, debug_log = self._build_outputs(**kwargs)
        return {"ui": {"preview_text": [full_prompt]}, "result": (full_prompt, debug_log)}


if HAS_SERVER:
    @PromptServer.instance.routes.post("/xaer_composer/get_layout")
    async def api_get_layout(request):
        data = await request.json()
        wildcard_dir = data.get("wildcard_dir", DEFAULT_WILDCARD_DIR)
        target_node = data.get("target_node", "pony")
        layout = build_node_layout(wildcard_dir, target_node)
        return web.json_response({"status": "ok", "layout": layout})

    @PromptServer.instance.routes.post("/xaer_composer/save_layout")
    async def api_save_layout(request):
        data = await request.json()
        wildcard_dir = data.get("wildcard_dir", DEFAULT_WILDCARD_DIR)
        target_node = data.get("target_node", "pony")
        layout = data.get("layout", {})
        config = load_or_init_config(wildcard_dir)
        config.setdefault("node_layouts", {})[target_node] = layout
        ok = save_config(wildcard_dir, config)
        return web.json_response({"status": "ok" if ok else "error"})

    @PromptServer.instance.routes.post("/xaer_composer/preview_prompt")
    async def api_preview_prompt(request):
        data = await request.json()
        target_node = data.get("target_node", "pony")
        params = data.get("params", {})
        node_map = {
            "pony": XaerPonyPromptComposer,
            "zimage": XaerZImagePromptComposer,
            "minimaxh3": XaerMiniMaxH3PromptComposer,
        }
        cls = node_map.get(target_node, XaerPonyPromptComposer)
        instance = cls()
        full_prompt, debug_log = instance._build_outputs(**params)
        return web.json_response({"status": "ok", "prompt": full_prompt, "debug": debug_log})