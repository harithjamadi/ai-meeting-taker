# Project Research Summary

**Project:** AI Meeting Taker
**Domain:** AI Meeting Assistants / Productivity Tools
**Researched:** 2026-03-14
**Confidence:** HIGH

## Executive Summary

The "AI Meeting Taker" is a productivity tool designed to automate the capture, transcription, and summarization of meetings, with a primary focus on high-quality Notion integration. Based on research, the most effective approach is to build a decoupled architecture that treats Notion as a primary export target while providing a robust local "Notion-like" experience for immediate review and privacy-conscious users. Experts in this space leverage Whisper for high-fidelity transcription and structured Pydantic models to feed LLMs (like Gemini/OpenAI/Ollama) for consistent summary and action item extraction.

The recommended technical strategy uses a Python-based backend for processing and the official Notion SDK for reliability. For the user interface, a "Notion-clone" aesthetic using Tailwind CSS and block-based editors (like BlockNote) is highly recommended to meet user expectations for modern documentation tools. This approach balances the power of cloud-based project management with the speed and privacy of local processing.

The primary technical risks involve Notion's strict API rate limits and the complexity of mapping nested block structures. To mitigate these, the architecture must include batching logic for block creation and a simplified UI schema that mirrors Notion's capabilities without exceeding API constraints. Early focus should be on the "Export Layer" to ensure data integrity before scaling to more complex features like real-time synchronization.

## Key Findings

### Recommended Stack

The stack focuses on the official Notion SDK for stability and modern frontend tools for a "Notion-like" local experience.

**Core technologies:**
- `notion-client` (>= 2.x): API Interaction — Official SDK supporting the latest version (2026-03-11).
- `pydantic` (>= 2.x): Data Modeling — Ensures strict schema validation for meeting minutes and action items.
- `Tailwind CSS` & `shadcn/ui`: Styling/UI — Provides the clean, accessible Notion aesthetic with minimal overhead.
- `BlockNote`: Editor/Viewer — The most accurate open-source block-based editor for local "Notion-like" rendering.
- `python-markdown`: HTML Generation — Standard parser with extension support for local exports.

### Expected Features

Users expect a seamless transition from raw audio to structured, actionable documents in Notion.

**Must have (table stakes):**
- Structured Summary — Quick review of meeting highlights (standard LLM output).
- Action Item Extraction — Turning talk into tasks with detected assignees/deadlines.
- Notion Export — Mapping meeting data to Notion database properties and page blocks.
- Full Transcript — For audit and deep-reference.

**Should have (competitive):**
- Notion-like Local UI — Privacy-first local viewer that mimics the Notion experience.
- Real-time Database Sync — Automatically updating external PM tools as meetings conclude.
- Audio-to-Note Link — Timestamped transcript segments linked to audio clips.

**Defer (v2+):**
- Native Video Recording — High infrastructure complexity; use existing meeting tool recordings instead.
- Synced Blocks — Highly specific Notion API complexity that is hard to mirror locally.

### Architecture Approach

A decoupled "Export Layer" is used to map an internal `MinutesModel` to multiple target formats (Notion, HTML, Markdown).

**Major components:**
1. `MinutesModel` — Central Pydantic model storing structured summary, actions, and transcript.
2. `NotionMapper` — Factory pattern to convert internal models into Notion-specific block JSON.
3. `LocalRenderer` — Custom Python-Markdown extension for generating Tailwind-styled HTML.
4. `DatabaseManager` — Handles Notion database ID discovery and dynamic property mapping.

### Critical Pitfalls

1. **Notion Rate Limiting** — Standard integrations are limited to ~3 requests/second; use block batching (`append_block_children`) to avoid 429 errors.
2. **Nested Block Complexity** — Notion API limits nesting levels; keep layouts simple (max 1 level of columns) to avoid 400 errors.
3. **Schema Drift** — User changes to Notion database properties can break exports; check schema via `databases.retrieve` before each run.
4. **Duplicate Action Items** — LLMs may repeat tasks; require a post-processing deduplication step.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Processing & Local Export
**Rationale:** Establishing the data pipeline from LLM to a local "Notion-like" format is the foundation of the app's value.
**Delivers:** Working Whisper transcription, structured summary extraction, and a local HTML viewer.
**Addresses:** Structured Summary, Full Transcript, Local Markdown Viewer.
**Avoids:** Duplicate Action Items (via initial deduplication logic).

### Phase 2: Advanced Notion Integration
**Rationale:** Once local data is reliable, the focus shifts to the primary external integration target.
**Delivers:** Mapping of meeting data to Notion databases and pages.
**Uses:** `notion-client`, `NotionMapper`, `DatabaseManager`.
**Implements:** Notion Export, Action Item Extraction (into properties).

### Phase 3: Enhanced Local UX & Refinement
**Rationale:** Improves the "Notion-like" aesthetic and adds polish based on integration feedback.
**Delivers:** A high-fidelity local UI and robust error handling for API failures.
**Addresses:** Notion-like Local UI, Real-time sync (basic).
**Avoids:** Rate Limiting (via implemented batching/retry logic).

### Phase Ordering Rationale

- **Dependency-Driven:** Local processing must be stable before attempting complex API exports to Notion.
- **Risk Mitigation:** Early focus on the `MinutesModel` ensures that even if Notion's API changes, the core data is preserved.
- **Architecture-Aligned:** Building the "Export Layer" components sequentially follows the recommended decoupled pattern.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Notion Integration):** Detailed research into specific database property mapping (Selects, Relations) and rate limit batching strategies.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Processing):** Whisper and basic LLM summarization are well-documented and standard.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Based on official Notion SDK and mature UI frameworks. |
| Features | HIGH | Aligned with market standards (Fireflies, Otter). |
| Architecture | MEDIUM | Decoupled export is solid, but Notion API layout mapping is notoriously finicky. |
| Pitfalls | HIGH | Well-documented API limits and common integration failures. |

**Overall confidence:** HIGH

### Gaps to Address

- **Speaker Diarization:** Whisper's default doesn't always handle multiple speakers perfectly; may need additional research if "who said what" is a hard requirement.
- **Large Audio Files:** Handling multi-hour meetings may require specific chunking strategies for both Whisper and LLM contexts.

## Sources

### Primary (HIGH confidence)
- [Notion API Reference (2026-03-11)](https://developers.notion.com/reference/) — Core integration logic.
- [BlockNote Documentation](https://www.blocknotejs.org/) — Local UI patterns.

### Secondary (MEDIUM confidence)
- [Fireflies.ai Feature List](https://fireflies.ai/features) — Competitive feature benchmarks.
- [Python-Markdown Extension API](https://python-markdown.github.io/extensions/api/) — Custom rendering logic.

---
*Research completed: 2026-03-14*
*Ready for roadmap: yes*
