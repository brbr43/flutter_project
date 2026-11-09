"""Genre / style templates for deterministic script→scene drafts.

No model downloads. Pure data used by the template generator.
"""

from __future__ import annotations

from typing import Any, TypedDict


class BeatTemplate(TypedDict):
    id: str
    title: str
    summary: str


class SceneTemplate(TypedDict):
    title: str
    beat_id: str
    script_text: str
    camera: str
    lighting: str
    prompt: str
    content_tag: str  # fact | dramatization | fiction
    duration_hint_sec: int


class GenreTemplate(TypedDict):
    id: str
    label_en: str
    label_ar: str
    tone: str
    camera_default: str
    lighting_default: str
    prompt_suffix: str
    beats: list[BeatTemplate]
    scene_blueprints: list[SceneTemplate]


GENRE_TEMPLATES: dict[str, GenreTemplate] = {
    "documentary": {
        "id": "documentary",
        "label_en": "Documentary",
        "label_ar": "وثائقي",
        "tone": "observational, factual, measured narration",
        "camera_default": "static interview / observational B-roll",
        "lighting_default": "natural available light",
        "prompt_suffix": "documentary still, natural light, 35mm, shallow depth of field",
        "beats": [
            {"id": "hook", "title": "Hook", "summary": "Establish the real-world subject and stakes."},
            {"id": "context", "title": "Context", "summary": "Background facts and setting."},
            {"id": "evidence", "title": "Evidence", "summary": "Key fact or witness moment."},
            {"id": "tension", "title": "Tension", "summary": "Complication or conflict of interest."},
            {"id": "resolution", "title": "Resolution", "summary": "Outcome and lingering question."},
        ],
        "scene_blueprints": [
            {
                "title": "Opening observation",
                "beat_id": "hook",
                "script_text": "Wide establishing shot of the subject’s world. Narration states the central question.",
                "camera": "wide static establishing",
                "lighting": "natural daylight",
                "prompt": "documentary establishing shot, real location, natural light",
                "content_tag": "fact",
                "duration_hint_sec": 8,
            },
            {
                "title": "Context beat",
                "beat_id": "context",
                "script_text": "Archival or environmental detail that grounds the facts.",
                "camera": "medium observational",
                "lighting": "soft window light",
                "prompt": "documentary detail insert, archival mood, soft natural light",
                "content_tag": "fact",
                "duration_hint_sec": 6,
            },
            {
                "title": "Evidence moment",
                "beat_id": "evidence",
                "script_text": "A concrete fact or testimony is presented without embellishment.",
                "camera": "close interview / object insert",
                "lighting": "practical lamps",
                "prompt": "documentary interview insert, honest framing, practical light",
                "content_tag": "fact",
                "duration_hint_sec": 7,
            },
            {
                "title": "Dramatized bridge (optional)",
                "beat_id": "tension",
                "script_text": "A lightly dramatized recreation marks uncertainty — clearly tagged.",
                "camera": "handheld subjective",
                "lighting": "low-key chiaroscuro",
                "prompt": "tasteful dramatized recreation, muted palette, documentary hybrid",
                "content_tag": "dramatization",
                "duration_hint_sec": 5,
            },
            {
                "title": "Closing reflection",
                "beat_id": "resolution",
                "script_text": "Return to the subject; leave the open question on screen.",
                "camera": "slow push-in",
                "lighting": "golden hour / dusk",
                "prompt": "documentary closing frame, contemplative, golden hour",
                "content_tag": "fact",
                "duration_hint_sec": 6,
            },
        ],
    },
    "hollywood": {
        "id": "hollywood",
        "label_en": "Hollywood",
        "label_ar": "هوليوود",
        "tone": "high-stakes, three-act spectacle, clear protagonist goal",
        "camera_default": "cinematic coverage, motivated moves",
        "lighting_default": "high production key + rim",
        "prompt_suffix": "hollywood cinematic, anamorphic, film grain, dramatic lighting",
        "beats": [
            {"id": "setup", "title": "Setup", "summary": "World and hero introduced."},
            {"id": "inciting", "title": "Inciting Incident", "summary": "The call that changes everything."},
            {"id": "midpoint", "title": "Midpoint", "summary": "Reversal that raises stakes."},
            {"id": "climax", "title": "Climax", "summary": "Final confrontation."},
            {"id": "tag", "title": "Tag", "summary": "Emotional button / aftermath."},
        ],
        "scene_blueprints": [
            {
                "title": "Hero introduced",
                "beat_id": "setup",
                "script_text": "Hero in their ordinary world; a visual motif foreshadows the goal.",
                "camera": "tracking medium",
                "lighting": "warm key, soft fill",
                "prompt": "cinematic hero introduction, anamorphic bokeh, warm key light",
                "content_tag": "fiction",
                "duration_hint_sec": 6,
            },
            {
                "title": "Inciting moment",
                "beat_id": "inciting",
                "script_text": "A sudden event forces the hero to act.",
                "camera": "crash zoom / whip pan into close-up",
                "lighting": "hard contrast",
                "prompt": "dramatic inciting incident, high contrast, cinematic",
                "content_tag": "fiction",
                "duration_hint_sec": 5,
            },
            {
                "title": "Midpoint reversal",
                "beat_id": "midpoint",
                "script_text": "Allies fail; the true cost becomes clear.",
                "camera": "over-shoulder then pull-back",
                "lighting": "cool moonlight vs warm practicals",
                "prompt": "midpoint reveal, cool vs warm contrast, cinematic",
                "content_tag": "fiction",
                "duration_hint_sec": 7,
            },
            {
                "title": "Climax showdown",
                "beat_id": "climax",
                "script_text": "Hero faces the antagonist / obstacle in a decisive beat.",
                "camera": "dynamic handheld + epic wide",
                "lighting": "high-drama volumetric",
                "prompt": "epic climax, volumetric light, cinematic action frame",
                "content_tag": "fiction",
                "duration_hint_sec": 8,
            },
            {
                "title": "Emotional tag",
                "beat_id": "tag",
                "script_text": "Quiet aftermath; motif returns transformed.",
                "camera": "slow dolly out",
                "lighting": "soft dawn",
                "prompt": "emotional aftermath, soft dawn light, cinematic still",
                "content_tag": "fiction",
                "duration_hint_sec": 5,
            },
        ],
    },
    "mystery": {
        "id": "mystery",
        "label_en": "Mystery",
        "label_ar": "غموض",
        "tone": "clues, misdirection, rising dread",
        "camera_default": "subjective POVs and inserts of clues",
        "lighting_default": "low-key, practical shadows",
        "prompt_suffix": "mystery thriller, noir shadows, moody color grade",
        "beats": [
            {"id": "crime", "title": "The Puzzle", "summary": "Something is wrong."},
            {"id": "suspect", "title": "Suspects", "summary": "Conflicting testimonies."},
            {"id": "clue", "title": "Clue", "summary": "A detail that shouldn’t fit."},
            {"id": "twist", "title": "Twist", "summary": "Assumption collapses."},
            {"id": "reveal", "title": "Reveal", "summary": "Truth comes into focus."},
        ],
        "scene_blueprints": [
            {
                "title": "Puzzle discovered",
                "beat_id": "crime",
                "script_text": "Investigator finds the first anomaly.",
                "camera": "slow push toward object",
                "lighting": "single practical lamp",
                "prompt": "mystery discovery, single practical lamp, noir",
                "content_tag": "fiction",
                "duration_hint_sec": 6,
            },
            {
                "title": "Conflicting accounts",
                "beat_id": "suspect",
                "script_text": "Two people describe the same night differently.",
                "camera": "shot-reverse-shot",
                "lighting": "uneven practicals",
                "prompt": "tense interrogation, uneven practical light, thriller",
                "content_tag": "fiction",
                "duration_hint_sec": 7,
            },
            {
                "title": "Odd detail",
                "beat_id": "clue",
                "script_text": "A small clue reframes earlier scenes.",
                "camera": "extreme close-up insert",
                "lighting": "hard side light",
                "prompt": "clue insert extreme close-up, hard side light, mystery",
                "content_tag": "fiction",
                "duration_hint_sec": 4,
            },
            {
                "title": "Assumption breaks",
                "beat_id": "twist",
                "script_text": "The trusted explanation collapses.",
                "camera": "dutch angle",
                "lighting": "flicker / unstable",
                "prompt": "twist reveal, dutch angle, unstable light, thriller",
                "content_tag": "fiction",
                "duration_hint_sec": 6,
            },
            {
                "title": "Truth revealed",
                "beat_id": "reveal",
                "script_text": "The puzzle pieces lock; a quiet confirmation shot.",
                "camera": "locked-off wide then cut to eyes",
                "lighting": "clearing dawn light",
                "prompt": "mystery resolution, clearing light, restrained framing",
                "content_tag": "fiction",
                "duration_hint_sec": 6,
            },
        ],
    },
    "historical": {
        "id": "historical",
        "label_en": "Historical",
        "label_ar": "تاريخي",
        "tone": "period atmosphere, careful fact vs dramatization labeling",
        "camera_default": "composed tableaux and motivated tracking",
        "lighting_default": "period-accurate sources (candles, sun, gas)",
        "prompt_suffix": "historical period drama, accurate costumes, filmic",
        "beats": [
            {"id": "era", "title": "Era", "summary": "Place and time established."},
            {"id": "figures", "title": "Figures", "summary": "Key historical people introduced."},
            {"id": "event", "title": "Event", "summary": "Documented turning point."},
            {"id": "human", "title": "Human Cost", "summary": "Personal consequence (may be dramatized)."},
            {"id": "legacy", "title": "Legacy", "summary": "What remains after."},
        ],
        "scene_blueprints": [
            {
                "title": "Period establishing",
                "beat_id": "era",
                "script_text": "City / landscape of the era; on-screen date (fact).",
                "camera": "wide crane / locked tableau",
                "lighting": "period sun / overcast",
                "prompt": "historical establishing shot, period architecture, natural light",
                "content_tag": "fact",
                "duration_hint_sec": 7,
            },
            {
                "title": "Historical figures",
                "beat_id": "figures",
                "script_text": "Named figures enter a documented setting.",
                "camera": "medium composed",
                "lighting": "candle / window period light",
                "prompt": "period drama medium shot, candlelight, historical costume",
                "content_tag": "fact",
                "duration_hint_sec": 6,
            },
            {
                "title": "Documented turning point",
                "beat_id": "event",
                "script_text": "The recorded event unfolds with restraint.",
                "camera": "observational wide",
                "lighting": "stark daylight",
                "prompt": "historical turning point, restrained framing, documentary-leaning",
                "content_tag": "fact",
                "duration_hint_sec": 8,
            },
            {
                "title": "Human cost (dramatized)",
                "beat_id": "human",
                "script_text": "A dramatized private moment shows the human cost — clearly tagged.",
                "camera": "intimate close-up",
                "lighting": "low warm lamp",
                "prompt": "intimate historical dramatization, warm lamp, emotional close-up",
                "content_tag": "dramatization",
                "duration_hint_sec": 5,
            },
            {
                "title": "Legacy",
                "beat_id": "legacy",
                "script_text": "Aftermath and what history kept.",
                "camera": "slow pull-back",
                "lighting": "fading dusk",
                "prompt": "historical aftermath, fading dusk, contemplative",
                "content_tag": "fact",
                "duration_hint_sec": 6,
            },
        ],
    },
    "drama": {
        "id": "drama",
        "label_en": "Drama",
        "label_ar": "دراما",
        "tone": "character-driven emotional arcs",
        "camera_default": "intimate coverage, held takes",
        "lighting_default": "motivated naturalistic",
        "prompt_suffix": "intimate drama, naturalistic lighting, 50mm",
        "beats": [
            {"id": "ordinary", "title": "Ordinary", "summary": "Daily life and desire."},
            {"id": "fracture", "title": "Fracture", "summary": "Relationship under pressure."},
            {"id": "choice", "title": "Choice", "summary": "A decision that can’t be undone."},
            {"id": "fallout", "title": "Fallout", "summary": "Emotional consequences."},
            {"id": "grace", "title": "Grace / Denial", "summary": "Acceptance or refusal."},
        ],
        "scene_blueprints": [
            {
                "title": "Ordinary day",
                "beat_id": "ordinary",
                "script_text": "Character in a quiet routine that reveals want.",
                "camera": "held medium",
                "lighting": "soft window",
                "prompt": "intimate drama, soft window light, 50mm",
                "content_tag": "fiction",
                "duration_hint_sec": 6,
            },
            {
                "title": "Pressure",
                "beat_id": "fracture",
                "script_text": "A conversation turns; silence says more than dialogue.",
                "camera": "two-shot then singles",
                "lighting": "practical kitchen / room lights",
                "prompt": "tense dialogue, practical room light, drama",
                "content_tag": "fiction",
                "duration_hint_sec": 8,
            },
            {
                "title": "Irreversible choice",
                "beat_id": "choice",
                "script_text": "The character acts; the frame holds the consequence.",
                "camera": "close-up held",
                "lighting": "hard noon / stark",
                "prompt": "decision close-up, stark naturalistic light, drama",
                "content_tag": "fiction",
                "duration_hint_sec": 5,
            },
            {
                "title": "Fallout",
                "beat_id": "fallout",
                "script_text": "Aftermath in empty spaces.",
                "camera": "wide lonely frame",
                "lighting": "cool overcast",
                "prompt": "lonely wide frame, cool overcast, emotional drama",
                "content_tag": "fiction",
                "duration_hint_sec": 6,
            },
            {
                "title": "Grace or denial",
                "beat_id": "grace",
                "script_text": "A final look — acceptance, or the door left closed.",
                "camera": "slow push to eyes",
                "lighting": "soft dusk",
                "prompt": "final emotional beat, soft dusk, intimate drama",
                "content_tag": "fiction",
                "duration_hint_sec": 5,
            },
        ],
    },
    "adventure": {
        "id": "adventure",
        "label_en": "Adventure",
        "label_ar": "مغامرة",
        "tone": "journey, set pieces, discovery",
        "camera_default": "dynamic wides and travel coverage",
        "lighting_default": "bright exteriors / torchlit interiors",
        "prompt_suffix": "adventure epic, travel vistas, dynamic composition",
        "beats": [
            {"id": "call", "title": "Call", "summary": "The journey begins."},
            {"id": "threshold", "title": "Threshold", "summary": "Leaving the known world."},
            {"id": "trial", "title": "Trial", "summary": "Obstacle / set piece."},
            {"id": "discovery", "title": "Discovery", "summary": "What they came for — with a cost."},
            {"id": "return", "title": "Return", "summary": "Changed by the road."},
        ],
        "scene_blueprints": [
            {
                "title": "Call to journey",
                "beat_id": "call",
                "script_text": "A map, a message, or a horizon pulls the hero out.",
                "camera": "wide vista + insert of map/object",
                "lighting": "bright morning",
                "prompt": "adventure call to journey, bright morning vista",
                "content_tag": "fiction",
                "duration_hint_sec": 6,
            },
            {
                "title": "Crossing the threshold",
                "beat_id": "threshold",
                "script_text": "Leaving home behind; landscape shifts.",
                "camera": "traveling tracking shot",
                "lighting": "harsh sun",
                "prompt": "threshold crossing, traveling shot, harsh sun, adventure",
                "content_tag": "fiction",
                "duration_hint_sec": 5,
            },
            {
                "title": "Trial set piece",
                "beat_id": "trial",
                "script_text": "Obstacle demands ingenuity, not just force.",
                "camera": "dynamic handheld + epic wide",
                "lighting": "storm / torch",
                "prompt": "adventure trial set piece, dynamic composition, storm light",
                "content_tag": "fiction",
                "duration_hint_sec": 8,
            },
            {
                "title": "Discovery",
                "beat_id": "discovery",
                "script_text": "The prize appears — and its price becomes clear.",
                "camera": "reveal tilt / crane",
                "lighting": "shaft of light / cavern glow",
                "prompt": "discovery reveal, shaft of light, adventure wonder",
                "content_tag": "fiction",
                "duration_hint_sec": 7,
            },
            {
                "title": "Return changed",
                "beat_id": "return",
                "script_text": "Home again, but the traveler’s eyes have changed.",
                "camera": "slow walk toward camera",
                "lighting": "soft evening",
                "prompt": "return home changed, soft evening light, adventure coda",
                "content_tag": "fiction",
                "duration_hint_sec": 5,
            },
        ],
    },
}

GENRE_IDS: tuple[str, ...] = tuple(GENRE_TEMPLATES.keys())

CONTENT_TAGS = ("fact", "dramatization", "fiction")


def get_genre(genre_id: str) -> GenreTemplate:
    key = (genre_id or "drama").strip().lower()
    if key not in GENRE_TEMPLATES:
        raise KeyError(f"Unknown genre '{genre_id}'. Allowed: {', '.join(GENRE_IDS)}")
    return GENRE_TEMPLATES[key]


def genre_catalog() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for g in GENRE_TEMPLATES.values():
        out.append(
            {
                "id": g["id"],
                "label_en": g["label_en"],
                "label_ar": g["label_ar"],
                "tone": g["tone"],
                "beat_count": len(g["beats"]),
                "default_scene_count": len(g["scene_blueprints"]),
            }
        )
    return out
