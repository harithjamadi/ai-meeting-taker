# Architecture Patterns: Meeting Export

**Domain:** AI Meeting Taker
**Researched:** 2026-03-14

## Recommended Architecture

A decoupled "Export Layer" that maps an internal `MeetingMinutes` model to multiple target formats (Notion Block JSON, Local HTML/Tailwind, Markdown).

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `MinutesModel` | Stores structured summary, actions, transcript. | Processor, Exporters |
| `NotionMapper` | Converts `MinutesModel` to Notion-specific block types. | Notion API Client |
| `LocalRenderer` | Converts `MinutesModel` to a Tailwind-styled HTML document. | Filesystem |
| `DatabaseManager` | Handles database ID discovery and page property mapping. | Notion API Client |

### Data Flow

1. **LLM Processor** generates structured JSON (`MeetingMinutes`).
2. **Exporters** receive the model.
3. **NotionMapper** builds a list of blocks (Heading 1 for title, Callout for summary, Columns for metadata).
4. **NotionClient** makes a `pages.create` request using the `database_id` as parent.
5. **LocalRenderer** uses a custom Python-Markdown extension to generate a Notion-like HTML file.

## Patterns to Follow

### Pattern 1: Block JSON Factory
Encapsulate Notion block creation into small, reusable functions.
```python
def create_callout(text, icon="⭐", color="default"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"text": {"content": text}}],
            "icon": {"emoji": icon},
            "color": color
        }
    }
```

### Pattern 2: Tailored Markdown Styles
Use a custom `Treeprocessor` to inject Tailwind classes into local Markdown exports (as shown in research).

## Anti-Patterns to Avoid

### Anti-Pattern: Hardcoded Block IDs
**What:** Mapping directly to a specific user's Notion page/database ID.
**Why bad:** Makes the app non-portable and fragile.
**Instead:** Use configuration files or an interactive "Database Selector" via the Notion API.

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| Notion Rate Limits | None (serial) | Need queue/retry. | Webhooks & distributed queues. |
| File Storage | Local folder | S3 / Cloud Storage. | Content Delivery Network. |

## Sources

- [Notion Developers: Working with Blocks](https://developers.notion.com/docs/working-with-blocks)
- [Python-Markdown Extension API](https://python-markdown.github.io/extensions/api/)
