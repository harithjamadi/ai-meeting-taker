"""Audience-specific recap generator.

After a meeting is summarized, the user can ask for additional outputs
shaped for a specific audience or purpose — a Slack update, a follow-up
email, an executive summary, or a translation. Mirrors Notion's "follow-up
creation via simple prompts" workflow.
"""

from typing import Dict


RECAP_PRESETS: Dict[str, str] = {
    "slack": (
        "Draft a short Slack-style update (2-4 sentences, casual but informative). "
        "Use plain text — no markdown headings. Lead with the headline outcome."
    ),
    "email": (
        "Draft a professional follow-up email summarizing the meeting and next steps. "
        "Include a subject line, a short greeting, 3-5 bullet points of key takeaways, "
        "explicit action items with owners, and a polite closing."
    ),
    "exec": (
        "Draft a 3-bullet executive summary for senior leadership. "
        "Focus only on outcomes, decisions, and risks. No process detail."
    ),
    "engineering": (
        "Draft a technical recap aimed at engineers. Focus on technical decisions, "
        "architectural choices, blockers, and engineering action items. Use code/technical "
        "terms precisely."
    ),
    "tweet": (
        "Draft a single tweet (≤280 characters) capturing the gist. Plain text only."
    ),
    "translate-malay": (
        "Translate the meeting summary into Bahasa Malaysia, preserving the section "
        "structure and any Obsidian [[bracket links]]."
    ),
    "translate-japanese": (
        "Translate the meeting summary into Japanese, preserving the section structure "
        "and any Obsidian [[bracket links]]."
    ),
}


def build_recap_prompt(preset_or_custom: str, minutes_markdown: str, transcript: str) -> str:
    """Build a recap prompt. `preset_or_custom` is either a key in RECAP_PRESETS
    or a free-form instruction provided by the user."""
    instruction = RECAP_PRESETS.get(preset_or_custom, preset_or_custom)
    transcript_excerpt = (transcript or "")[:8000]
    return (
        "You are a helpful AI assistant. The user has already received the meeting "
        "summary below. Produce a follow-up recap shaped per the instruction.\n\n"
        f"INSTRUCTION:\n{instruction}\n\n"
        f"MEETING SUMMARY (already produced):\n{minutes_markdown}\n\n"
        f"RAW TRANSCRIPT (excerpt for grounding):\n{transcript_excerpt}\n\n"
        "Output ONLY the recap text. No preamble, no commentary, no surrounding code fences."
    )
