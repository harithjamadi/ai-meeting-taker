# Feature Landscape: AI Meeting Notes

**Domain:** AI Meeting Assistants
**Researched:** 2026-03-14

## Table Stakes

Features users expect in an AI meeting app in 2026.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Structured Summary | Quick review of what happened. | Low (LLM) | Standard in all meeting apps. |
| Action Item Extraction | Turning talk into tasks. | Medium | Requires clear "Assignee" and "Deadline" detection. |
| Notion Export | The industry standard for project management. | Medium | Requires mapping to block JSON. |
| Full Transcript | For audit and reference. | Medium | Needs speaker identification. |

## Differentiators

Features that set a product apart from basic transcription tools.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Notion-like Local UI | Privacy + same DX as the cloud. | High | Requires block-based local viewer. |
| Real-time Database Sync | Actions automatically appear in a PM tool. | High | Requires robust API integration. |
| Synced Blocks | Update meeting notes in one place, they update everywhere. | High | Notion specific, hard to implement locally. |
| Audio-to-Note Link | Click a summary sentence to hear the audio clip. | High | Requires timestamped transcription. |

## Anti-Features

Features to explicitly NOT build to avoid bloat.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Native Video Recording | Heavy infrastructure, GDPR/privacy nightmare. | Use existing tools (Zoom/Meet/Teams) and process audio. |
| Full Project Management | Don't compete with Notion/Linear. | Integrate with them deeply. |
| Built-in Calendar | Calendar market is saturated. | Use Notion Calendar or Google/Outlook sync. |

## Feature Dependencies

```
Transcription → Summary extraction → Action Item extraction → Export to Notion
Summary extraction → Local Markdown Export
Action Items → Relation to external "Tasks" database
```

## MVP Recommendation

Prioritize:
1. **Advanced Notion Export:** Use a database with `Date`, `Attendees`, and `Summary` properties.
2. **Local Markdown Viewer:** Provide a clean, Notion-like local HTML file.
3. **Structured Action Items:** Extract specific `Task` and `Assignee` fields for checkboxes.

Defer: **Real-time Sync** (complexity/cost), **Synced Blocks** (API only).

## Sources

- [Notion AI Meeting Notes Feature](https://www.notion.so/product/ai)
- [Fireflies.ai Feature List](https://fireflies.ai/features)
- [Otter.ai Feature List](https://otter.ai/)
