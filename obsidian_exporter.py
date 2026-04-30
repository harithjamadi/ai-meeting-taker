import os
from datetime import datetime
from typing import Optional

from config import OBSIDIAN_VAULT_PATH, MeetingMinutes, logger


class ObsidianExporter:
    """Exports MeetingMinutes to Obsidian-compatible Markdown.

    Renders the variable-length `sections` list (driven by the chosen meeting
    style) instead of a fixed summary/decisions template. Empty optional
    blocks are omitted entirely rather than printing 'None recorded'.
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.base_dir = output_dir or OBSIDIAN_VAULT_PATH
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Obsidian Vault Root: {os.path.abspath(self.base_dir)}")

    # ─────────────────────────────────────────────────────────────────
    # Path helpers
    # ─────────────────────────────────────────────────────────────────
    def _get_target_dir(self, date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            dt = datetime.now()
        target_path = os.path.join(self.base_dir, dt.strftime("%Y"), dt.strftime("%m"))
        os.makedirs(target_path, exist_ok=True)
        return target_path

    @staticmethod
    def _safe_title(title: str) -> str:
        return "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip() or "Meeting"

    @staticmethod
    def _unique_path(target_dir: str, base: str, ext: str) -> str:
        path = os.path.join(target_dir, f"{base}{ext}")
        counter = 1
        while os.path.exists(path):
            path = os.path.join(target_dir, f"{base} ({counter}){ext}")
            counter += 1
        return path

    # ─────────────────────────────────────────────────────────────────
    # Rendering
    # ─────────────────────────────────────────────────────────────────
    def render_markdown(self, minutes: MeetingMinutes) -> str:
        lines = []

        # Frontmatter
        lines.append("---")
        lines.append(f'title: "{self._yaml_escape(minutes.title)}"')
        lines.append(f"date: {minutes.date}")
        lines.append("type: meeting")
        lines.append(f'style: "{minutes.style}"')
        lines.append(f'tone: "{minutes.tone}"')
        lines.append(f'language: "{minutes.language}"')
        lines.append(f'sentiment: "{minutes.sentiment}"')
        if minutes.topics:
            lines.append("topics:")
            for topic in minutes.topics:
                lines.append(f'  - "{self._yaml_escape(topic)}"')
        lines.append("tags:")
        lines.append("  - meeting")
        lines.append(f"  - style/{minutes.style}")
        lines.append("  - ai-summary")
        lines.append("---")
        lines.append("")

        # Header
        lines.append(f"# {minutes.title}")
        lines.append("")
        lines.append(
            f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  "
        )
        lines.append(
            f"**Style:** {minutes.style}  •  **Tone:** {minutes.tone}  •  **Language:** {minutes.language}"
        )
        lines.append("")

        # Sections (the body)
        for section in minutes.sections:
            icon = section.icon or "abstract"
            lines.append(f"> [!{icon}] {section.heading}")
            for body_line in (section.body or "").split("\n"):
                lines.append(f"> {body_line}" if body_line else ">")
            lines.append("")

        # Key decisions (only if non-empty)
        if minutes.key_decisions:
            lines.append("> [!info] Key Decisions")
            for decision in minutes.key_decisions:
                lines.append(f"> - {decision}")
            lines.append("")

        # Action items (only if non-empty)
        if minutes.action_items:
            lines.append("## 🛠️ Action Items")
            lines.append("")
            for item in minutes.action_items:
                bits = []
                if item.assignee:
                    bits.append(f"**{item.assignee}**:")
                bits.append(item.task)
                trail = []
                if item.due:
                    trail.append(f"📅 {item.due}")
                if item.priority:
                    trail.append(f"⚡{item.priority}")
                trail_str = ("  " + "  ".join(trail)) if trail else ""
                lines.append(f"- [ ] {' '.join(bits)}{trail_str} #task")
            lines.append("")

        # Topics
        if minutes.topics:
            lines.append("## 📌 Topics")
            lines.append("")
            for topic in minutes.topics:
                lines.append(f"- {topic}")
            lines.append("")

        # Custom instructions (so user can re-run reproducibly)
        if minutes.custom_instructions:
            lines.append("> [!note]- Custom Instructions Used")
            for ci_line in minutes.custom_instructions.split("\n"):
                lines.append(f"> {ci_line}")
            lines.append("")

        # Transcript (collapsed)
        if minutes.transcript:
            lines.append("---")
            lines.append("")
            lines.append("## 📝 Full Transcript")
            lines.append("<details>")
            lines.append("<summary>Click to expand</summary>")
            lines.append("")
            lines.append(minutes.transcript)
            lines.append("")
            lines.append("</details>")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _yaml_escape(value: str) -> str:
        return (value or "").replace('"', '\\"')

    # ─────────────────────────────────────────────────────────────────
    # File writing
    # ─────────────────────────────────────────────────────────────────
    def export_to_file(self, minutes: MeetingMinutes) -> Optional[str]:
        target_dir = self._get_target_dir(minutes.date)
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M")
        safe_title = self._safe_title(minutes.title)
        md_path = self._unique_path(target_dir, f"{safe_title} - {timestamp}", ".md")
        logger.info(f"Exporting to Obsidian: {md_path}")

        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(self.render_markdown(minutes))
            logger.info("Successfully exported to Obsidian format.")
            return md_path
        except OSError as e:
            logger.error(f"Failed to export to Obsidian: {e}")
            return None

    def append_recap(self, md_path: str, label: str, recap_text: str) -> bool:
        """Append an audience-specific recap section to an existing meeting file."""
        try:
            with open(md_path, "a", encoding="utf-8") as f:
                f.write("\n---\n\n")
                f.write(f"## 🪄 Recap — {label}\n\n")
                f.write(recap_text.rstrip())
                f.write("\n")
            return True
        except OSError as e:
            logger.error(f"Failed to append recap: {e}")
            return False
