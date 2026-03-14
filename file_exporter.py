import os
from datetime import datetime
from config import logger, MeetingMinutes


class FileExporter:
    """Exports MeetingMinutes to local files.

    Output format: Markdown (.md) for rich rendering support (Notion, GitHub,
    Obsidian, etc.), plus an optional raw transcript file.
    """

    def __init__(self, output_dir: str = "meeting-content"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Output directory: {os.path.abspath(self.output_dir)}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_title(self, title: str) -> str:
        """Strip filesystem-unsafe characters from a meeting title."""
        return "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).strip()

    def _unique_path(self, base: str, ext: str) -> str:
        """Return a path that does not already exist, appending (n) if needed."""
        path = os.path.join(self.output_dir, f"{base}{ext}")
        if not os.path.exists(path):
            return path
        counter = 1
        while os.path.exists(path):
            path = os.path.join(self.output_dir, f"{base} ({counter}){ext}")
            counter += 1
        return path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_to_file(self, minutes: MeetingMinutes) -> str | None:
        """Write meeting minutes to a Markdown file.

        Returns the absolute path to the created file, or None on failure.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M")
        safe_title = self._safe_title(minutes.title)
        base_name = f"{safe_title} - {timestamp}"

        md_path = self._unique_path(base_name, ".md")
        logger.info(f"Exporting meeting minutes to: {md_path}")

        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(f"# {minutes.title}\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                f.write("---\n\n")

                f.write("## Summary\n\n")
                f.write(f"{minutes.summary}\n\n")

                f.write("## Key Decisions\n\n")
                if minutes.key_decisions:
                    for decision in minutes.key_decisions:
                        f.write(f"- {decision}\n")
                else:
                    f.write("_No key decisions recorded._\n")
                f.write("\n")

                f.write("## Action Items\n\n")
                if minutes.action_items:
                    for item in minutes.action_items:
                        f.write(f"- [ ] **{item.assignee}** — {item.task}\n")
                else:
                    f.write("_No action items recorded._\n")
                f.write("\n")

                if minutes.transcript:
                    f.write("---\n\n## Full Transcript\n\n")
                    f.write(f"{minutes.transcript}\n")

            logger.info("Successfully exported meeting minutes.")
            print(f"\n✅ Saved to: {os.path.abspath(md_path)}")
            return md_path

        except OSError as e:
            logger.error(f"Failed to export meeting minutes: {e}")
            return None