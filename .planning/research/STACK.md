# Technology Stack: Notion & Data Export

**Project:** AI Meeting Taker
**Researched:** 2026-03-14

## Recommended Stack

### Core Notion Integration
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `notion-client` | >= 2.x | API Interaction | Official SDK, supports version `2026-03-11`. |
| `pydantic` | >= 2.x | Data Modeling | Strict schema validation for meeting minutes. |

### Local UI (Notion-like)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `Tailwind CSS` | v3.x+ | Styling | Flexible, utility-first; supports `prose` (Typography). |
| `shadcn/ui` | Latest | UI Components | Provides the clean, accessible Notion aesthetic. |
| `BlockNote` | Latest | Editor/Viewer | Most accurate open-source block-based editor. |
| `Inter` font | Latest | Typography | The official typeface (or closest match) for Notion. |

### Markdown & Processing
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-markdown` | Latest | HTML Generation | Standard Python Markdown parser with extension support. |
| `Markdown-it-py` | Latest | Advanced Parsing | For more complex plugins (containers, etc). |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Notion Client | `notionhq/client` | `requests` (Raw API) | Handling pagination and rate limits is easier with the SDK. |
| Editor | `BlockNote` | `Novel` | Novel is heavily tied to Vercel/Next.js/AI SDK; BlockNote is more modular. |
| Styling | `Tailwind CSS` | `Chakra UI` | Tailwind's Typography plugin is superior for Markdown/Notion-like content. |

## Installation

### Python
```bash
# Core
pip install notion-client pydantic markdown

# Dev dependencies
pip install pytest black ruff
```

### Local UI (Frontend)
```bash
# React + Tailwind
npx create-next-app@latest my-notion-ui --typescript --tailwind --eslint

# Components
npx shadcn-ui@latest init
npm install @blocknote/core @blocknote/react
```

## Sources

- [Notion API Reference (2026-03-11)](https://developers.notion.com/reference/)
- [BlockNote Documentation](https://www.blocknotejs.org/)
- [Novel AI Editor](https://novel.sh/)
- [Tailwind Typography Plugin](https://tailwindcss.com/docs/typography-plugin)
