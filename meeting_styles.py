"""Meeting style presets, tone & length controls, and dynamic prompt builder.

This module is the personality engine. Instead of forcing every transcript
into a rigid 'title / summary / decisions / action items' shape, the AI
adapts its sections, voice, and structure to the kind of conversation it
just heard — closer to how Notion AI Meeting Notes behaves.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MeetingStyle:
    key: str
    name: str
    icon: str
    description: str
    sections: List[Dict[str, str]] = field(default_factory=list)
    extract_action_items: bool = True
    extract_decisions: bool = True
    voice: str = ""


STYLES: Dict[str, MeetingStyle] = {
    "auto": MeetingStyle(
        key="auto",
        name="Auto-detect",
        icon="🪄",
        description="Detect the conversation type and adapt automatically",
        sections=[],
        voice=(
            "Adapt your voice to the content. Casual chat → warm and human. "
            "Lecture → educational. Standup → terse. Interview → evidence-driven."
        ),
    ),
    "team": MeetingStyle(
        key="team",
        name="Team Meeting",
        icon="👥",
        description="Multi-topic team sync with discussions and decisions",
        sections=[
            {"heading": "Summary", "icon": "abstract", "guidance": "2-3 paragraph overview of what was covered"},
            {"heading": "Discussion Highlights", "icon": "note", "guidance": "Key points raised under each topic"},
            {"heading": "Open Questions", "icon": "question", "guidance": "Unresolved items the group still owes an answer on"},
        ],
        voice="Clear and professional. Capture context and reasoning, not just bullets.",
    ),
    "standup": MeetingStyle(
        key="standup",
        name="Stand-up",
        icon="🏃",
        description="Daily/weekly status — yesterday / today / blockers",
        sections=[
            {"heading": "Yesterday", "icon": "check", "guidance": "What each person reported completing"},
            {"heading": "Today", "icon": "todo", "guidance": "Today's plan, per person"},
            {"heading": "Blockers", "icon": "warning", "guidance": "Any blockers raised; if none, omit"},
        ],
        extract_decisions=False,
        voice="Terse. Bullet-driven. Group by person if speakers are identified.",
    ),
    "1on1": MeetingStyle(
        key="1on1",
        name="1:1",
        icon="🤝",
        description="One-on-one between manager & report or peers",
        sections=[
            {"heading": "Discussion", "icon": "abstract", "guidance": "Topics covered in conversational order"},
            {"heading": "Feedback Exchanged", "icon": "info", "guidance": "Feedback in either direction; quote when meaningful"},
            {"heading": "Career & Growth", "icon": "tip", "guidance": "Development conversation, if any"},
        ],
        voice="Warm and respectful. Handle sensitive topics with care; never editorialize.",
    ),
    "sales": MeetingStyle(
        key="sales",
        name="Sales Call",
        icon="💼",
        description="Customer or prospect call",
        sections=[
            {"heading": "Customer Context", "icon": "info", "guidance": "Their situation, role, organization"},
            {"heading": "Needs & Pain Points", "icon": "warning", "guidance": "What they're trying to solve"},
            {"heading": "Objections", "icon": "question", "guidance": "Concerns they raised; if none, omit"},
            {"heading": "Buying Signals", "icon": "star", "guidance": "Positive indicators of intent"},
        ],
        voice="Crisp and sales-savvy. Surface buying signals and objections clearly.",
    ),
    "interview": MeetingStyle(
        key="interview",
        name="Interview",
        icon="🎤",
        description="Candidate interview or research interview",
        sections=[
            {"heading": "Background", "icon": "info", "guidance": "Candidate's experience and context"},
            {"heading": "Strengths", "icon": "check", "guidance": "Strong signals with evidence"},
            {"heading": "Concerns", "icon": "warning", "guidance": "Reservations or gaps observed"},
            {"heading": "Notable Quotes", "icon": "quote", "guidance": "Direct quotes worth preserving verbatim"},
        ],
        extract_decisions=False,
        voice="Neutral and evidence-driven. Quote directly when meaningful; never embellish.",
    ),
    "brainstorm": MeetingStyle(
        key="brainstorm",
        name="Brainstorm",
        icon="💡",
        description="Idea-generation session",
        sections=[
            {"heading": "Theme", "icon": "abstract", "guidance": "What was being explored"},
            {"heading": "Ideas Generated", "icon": "tip", "guidance": "All ideas raised, even half-baked ones"},
            {"heading": "Promising Directions", "icon": "star", "guidance": "Ideas the group reacted positively to"},
        ],
        extract_decisions=False,
        voice="Energetic and generous. Don't filter ideas prematurely. Preserve creative tangents.",
    ),
    "casual": MeetingStyle(
        key="casual",
        name="Casual Conversation",
        icon="☕",
        description="Friends, family, informal chat — not a 'meeting' at all",
        sections=[
            {"heading": "What Was Discussed", "icon": "abstract", "guidance": "Conversational summary in friendly prose, not bullets"},
            {"heading": "Memorable Moments", "icon": "quote", "guidance": "Quotes or moments worth remembering"},
        ],
        extract_action_items=False,
        extract_decisions=False,
        voice=(
            "Warm, human, narrative. NEVER force a corporate structure on a personal "
            "conversation. Skip 'action items' and 'decisions' entirely — those don't apply here."
        ),
    ),
    "lecture": MeetingStyle(
        key="lecture",
        name="Lecture / Talk",
        icon="🎓",
        description="One-to-many — class, conference talk, training",
        sections=[
            {"heading": "Topic", "icon": "abstract", "guidance": "What was taught and why"},
            {"heading": "Key Concepts", "icon": "info", "guidance": "Core ideas with brief explanations"},
            {"heading": "Examples & Stories", "icon": "quote", "guidance": "Illustrative material"},
            {"heading": "Takeaways", "icon": "tip", "guidance": "What the audience should remember"},
        ],
        extract_decisions=False,
        voice="Educational. Restructure for learning, not transcription order.",
    ),
}


TONES: Dict[str, str] = {
    "professional": "Clear, neutral, formal. Default business voice.",
    "friendly": "Warm and conversational. Contractions OK. Sound human, not robotic.",
    "concise": "Terse. Bullet-driven. No filler. Maximum signal density.",
    "detailed": "Thorough. Include context, examples, and nuance. Don't skim.",
    "witty": "Light, occasional dry humor while staying useful and respectful.",
}


LENGTHS: Dict[str, str] = {
    "brief": "Keep summary under 100 words. Lean every section heavily.",
    "standard": "Aim for a 200-400 word summary across sections. Balanced detail.",
    "comprehensive": "Aim for 500+ words. Deep detail with examples and quotes.",
}


CLASSIFY_PROMPT = (
    "You are a meeting classifier. Given a transcript excerpt, return ONE of these "
    "style keys that best fits the conversation:\n"
    "- standup (daily/weekly team status update)\n"
    "- 1on1 (manager↔report or peer 1:1)\n"
    "- team (multi-topic team meeting)\n"
    "- sales (customer or prospect call)\n"
    "- interview (candidate or research interview)\n"
    "- brainstorm (open idea generation)\n"
    "- lecture (one-to-many — class, talk, training)\n"
    "- casual (friends/family/informal chat — NOT a real meeting)\n\n"
    "Output ONLY the key, lowercase, no other text."
)


def build_classify_prompt() -> str:
    return CLASSIFY_PROMPT


def build_system_prompt(
    style_key: str,
    tone_key: str = "professional",
    length_key: str = "standard",
    language: str = "auto",
    custom_instructions: Optional[str] = None,
    pre_meeting_context: Optional[str] = None,
    speaker_map: Optional[Dict[str, str]] = None,
    obsidian_linking: bool = True,
) -> str:
    """Compose a system prompt that adapts to the chosen style and user preferences."""
    style = STYLES.get(style_key, STYLES["auto"])
    tone = TONES.get(tone_key, TONES["professional"])
    length = LENGTHS.get(length_key, LENGTHS["standard"])

    parts: List[str] = []
    parts.append(
        "You are an AI meeting assistant. Produce a faithful, well-organized "
        "summary of the transcript that the user provides."
    )

    parts.append(f"\n## Meeting Style: {style.name}\n{style.description}\n**Voice:** {style.voice}")
    parts.append(f"\n## Tone\n{tone}")
    parts.append(f"\n## Length\n{length}")

    if language and language.lower() != "auto":
        parts.append(
            f"\n## Output Language\nWrite the entire output in **{language}**. "
            "If the transcript is in another language, translate as needed."
        )
    else:
        parts.append("\n## Output Language\nMatch the dominant language of the transcript.")

    if pre_meeting_context:
        parts.append(
            "\n## Pre-Meeting Context (use this to ground accuracy — do not invent facts not present in the transcript)\n"
            f"{pre_meeting_context}"
        )

    if speaker_map:
        mapping = "\n".join(f"- {label} = {name}" for label, name in speaker_map.items())
        parts.append(
            "\n## Known Speakers\n"
            f"{mapping}\n"
            "Use the real names instead of 'Speaker N' labels."
        )

    if custom_instructions:
        parts.append(
            "\n## Custom Instructions (highest priority — override defaults if they conflict)\n"
            f"{custom_instructions}"
        )

    if style_key == "auto":
        parts.append(
            "\n## Output Sections\n"
            "Choose 2-5 sections that best fit the content. Examples: Summary, Highlights, "
            "Decisions, Q&A, Memorable Moments, Concepts, Takeaways. Do NOT force-fit empty "
            "sections — if there are no decisions, do not include a Decisions section. "
            "If the conversation is casual or personal, lean into a warm narrative summary "
            "and skip corporate scaffolding entirely."
        )
    else:
        section_lines = [f"- **{s['heading']}** — {s['guidance']}" for s in style.sections]
        parts.append("\n## Output Sections (in this order)\n" + "\n".join(section_lines))
        parts.append("If a section has no real content, omit it rather than writing 'None recorded'.")

    if obsidian_linking:
        parts.append(
            "\n## Obsidian Linking\n"
            "Wrap proper nouns (people's names, projects, products, significant technical "
            "terms) in [[double brackets]] across all sections — e.g. [[Abdullah]], [[MCP]], "
            "[[Python]]. Apply consistently. Do NOT bracket common words."
        )

    schema_extras: List[str] = []
    if style.extract_action_items:
        schema_extras.append(
            '"action_items": [{"task": "string", "assignee": "string", "due": "string|null", "priority": "high|medium|low|null"}]'
        )
    if style.extract_decisions:
        schema_extras.append('"key_decisions": ["string"]')
    optional_block = (",\n  " + ",\n  ".join(schema_extras)) if schema_extras else ""

    parts.append(
        "\n## Required JSON Output\n"
        "Output ONLY valid JSON. No preamble, no commentary outside the JSON object.\n"
        "{\n"
        '  "title": "Concise descriptive title that reflects what this conversation was actually about",\n'
        '  "language": "ISO 639-1 code, e.g. en, ms, ja",\n'
        '  "sections": [\n'
        '    {"heading": "string", "icon": "abstract|info|note|tip|warning|quote|todo|check|star|question", "body": "markdown string"}\n'
        "  ],\n"
        '  "topics": ["short tag-like topic"],\n'
        '  "sentiment": "Positive|Neutral|Negative"'
        f"{optional_block}\n"
        "}"
    )

    parts.append(
        "\n## Critical Rules\n"
        "1. Be faithful to the transcript. Never invent action items, decisions, or quotes.\n"
        "2. Match the tone and voice specified above.\n"
        "3. If something doesn't apply (e.g., no action items in a casual chat), omit the array — never fill it with placeholders.\n"
        "4. The title must reflect what was actually discussed, not a generic label like 'Meeting Summary'."
    )

    return "\n".join(parts)
