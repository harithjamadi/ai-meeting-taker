import os
from datetime import datetime
from config import logger, MeetingMinutes, OBSIDIAN_VAULT_PATH

class ObsidianExporter:
    """Exports MeetingMinutes to Obsidian-compatible Markdown files.

    Features:
    - YAML Frontmatter for metadata (Properties).
    - Obsidian Callouts for visual emphasis.
    - Markdown Task List formatting.
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or OBSIDIAN_VAULT_PATH
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Obsidian Vault/Folder: {os.path.abspath(self.output_dir)}")

    def _safe_title(self, title: str) -> str:
        """Strip filesystem-unsafe characters."""
        return "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()

    def _unique_path(self, base: str, ext: str) -> str:
        path = os.path.join(self.output_dir, f"{base}{ext}")
        if not os.path.exists(path):
            return path
        counter = 1
        while os.path.exists(path):
            path = os.path.join(self.output_dir, f"{base} ({counter}){ext}")
            counter += 1
        return path

    def export_to_file(self, minutes: MeetingMinutes) -> str | None:
        """Write meeting minutes to an Obsidian Markdown file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M")
        safe_title = self._safe_title(minutes.title)
        base_name = f"{safe_title} - {timestamp}"

        md_path = self._unique_path(base_name, ".md")
        logger.info(f"Exporting to Obsidian: {md_path}")

        try:
            with open(md_path, "w", encoding="utf-8") as f:
                # 1. YAML Frontmatter (Properties)
                f.write("---\n")
                f.write(f"title: \"{minutes.title}\"\n")
                f.write(f"date: {minutes.date}\n")
                f.write(f"type: meeting\n")
                f.write(f"sentiment: {minutes.sentiment}\n")
                if minutes.topics:
                    f.write("topics:\n")
                    for topic in minutes.topics:
                        f.write(f"  - {topic}\n")
                f.write("tags: [meeting, ai-summary]\n")
                f.write("---\n\n")

                # 2. Header
                f.write(f"# {minutes.title}\n\n")
                f.write(f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

                # 3. Summary (Callout)
                f.write("> [!abstract] Summary\n")
                f.write("> " + minutes.summary.replace("\n", "\n> ") + "\n\n")

                # 4. Key Decisions (Callout)
                f.write("> [!info] Key Decisions\n")
                if minutes.key_decisions:
                    for decision in minutes.key_decisions:
                        f.write(f"> - {decision}\n")
                else:
                    f.write("> _No key decisions recorded._\n")
                f.write("\n")

                # 5. Action Items
                f.write("## 🛠️ Action Items\n\n")
                if minutes.action_items:
                    for item in minutes.action_items:
                        # Task list format for Obsidian
                        f.write(f"- [ ] **{item.assignee}**: {item.task} #task\n")
                else:
                    f.write("_No action items recorded._\n")
                f.write("\n")

                # 6. Topics
                f.write("## 📌 Topics Discussed\n\n")
                for topic in minutes.topics:
                    f.write(f"- {topic}\n")
                f.write("\n")

                # 7. Transcript (Collapsed toggle)
                if minutes.transcript:
                    f.write("---\n\n")
                    f.write("## 📝 Full Transcript\n")
                    f.write("<details>\n<summary>Click to expand</summary>\n\n")
                    f.write(minutes.transcript)
                    f.write("\n\n</details>\n")

            logger.info("Successfully exported to Obsidian format.")
            return md_path

        except OSError as e:
            logger.error(f"Failed to export to Obsidian: {e}")
            return None
