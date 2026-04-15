# Domain Pitfalls: Meeting Export & Notion Integration

**Domain:** AI Meeting Assistants
**Researched:** 2026-03-14

## Critical Pitfalls

Mistakes that cause major issues or require code rewrites.

### Pitfall 1: Rate Limiting
**What goes wrong:** Exporting a long meeting with many blocks (each transcript line as a block) hits Notion's rate limit.
**Why it happens:** Notion allows ~3 requests per second for standard integrations.
**Consequences:** Partial exports, failed pages, poor UX.
**Prevention:** Batch block creation using `append_block_children` or use larger text blocks (up to 2000 characters per paragraph).
**Detection:** `429 Too Many Requests` responses.

### Pitfall 2: Nested Block Complexity
**What goes wrong:** Trying to create complex layouts (Columns inside Columns) via the API.
**Why it happens:** Some nesting levels are restricted or require multiple API calls (one per level).
**Consequences:** API returns `400 Bad Request` or the layout looks broken in Notion.
**Prevention:** Keep layouts simple (1 level of columns) and verify each block's schema.

## Moderate Pitfalls

### Pitfall 1: Property Type Mismatches
**What goes wrong:** Trying to set a "Multi-select" property using a plain string.
**Prevention:** Always check the database schema via `databases.retrieve` before creating a page.

### Pitfall 2: Local HTML Styling
**What goes wrong:** Local Notion-like HTML doesn't look the same on all machines (missing Inter font, CSS issues).
**Prevention:** Use a CDN-hosted Tailwind CSS bundle or embed the CSS/Fonts directly in the export.

## Minor Pitfalls

### Pitfall 1: Markdown Flavor Differences
**What goes wrong:** Notion's Markdown (standard CommonMark + some GFM) vs Python-Markdown's default output.
**Prevention:** Use specific extensions (tables, fenced code) to match expectations.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Database Integration | Schema Drift (user changed DB properties) | Robust error handling, check schema on start. |
| Action Items | Duplicate extraction (same task twice) | LLM post-processing to deduplicate. |
| Local UI | Bundle size / Performance | Keep renderer lightweight (static HTML/CSS). |

## Sources

- [Notion Developers: Limits & Request Throttling](https://developers.notion.com/docs/request-limits)
- [Notion Community Forum: API Layout Discussions](https://notion.so)
