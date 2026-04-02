---
description: Automated Insight Refinement from Notion Research
---
# /refine-insights [page_id]

Parses a manually annotated Notion research page and extracts structured problems/solutions into the `Market Gap & Solution Analysis <ndb2>` database.

## Trigger Pattern
- **Underline**: Identified as a **Problem/Friction Point**.
- **Bold + Italic**: Identified as a **Suggested Solution**.
- **Color Highlight**: Captured as **CEO Strategic Feedback**.
- **Notion Comments**: Parsed for additional context and instructions.

## Logic Flow
1. **Identify Source**: Accepts a Notion Page ID (p#) or URL.
2. **Text Analysis**: 
   - Scans all `rich_text` segments in the page's blocks.
   - Extracts unique "Problem" entries from underlined text.
   - Extracts unique "Solution" entries from bold+italic text.
   - Groups related snippets by block parent or proximity.
3. **Comment Extraction**: Retrieves all comments associated with the page and its blocks.
4. **Database Mapping**:
   - Creates a new entry in `Market Gap & Solution Analysis <ndb2>` (ID: `335b7eb0-71bb-8074-a264-e7eb5181b5e6`).
   - Fields populated:
     - `Problem/Friction`: Concatenated underlined text.
     - `Problem Description`: Surrounding block content + extracted comments.
     - `Suggested Solution`: Extracted bold+italic text.
     - `Source Research`: Relation link back to the original page in `ndb1`.
     - `CTO Review Status`: Set to `Investigating` (default).
     - `CEO Strategic Feedback`: Mapping colored highlights to priority levels or tags.

## Execution
// turbo
1. Run `npx ts-node refiner.ts [page_id]` (Internal abstraction handled by Antigravity).
2. Report success with the link to the new `<ndb2>` entries.
