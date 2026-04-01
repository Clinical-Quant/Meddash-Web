---
description: Automated sequential market research and reporting workflow.
---

# Automated Market Research Workflow
// turbo-all

1. Use the `browser_subagent` to conduct a comprehensive search on the target competitor or market topic.
2. Research specifically: Product offerings, Data sources, Pricing tiers (Tiers A, B, C), and Customer sentiment.
3. Keep all links, sources, browse details, and social links. If there are social searches, the search results MUST be kept verbatim.
4. Synthesize the findings into a structured markdown scratchpad.
5. Upload all details from the scratchpad to the corresponding Notion page within the `Meddash-Product Manager` workspace.
6. Organize the Notion page carefully: **DO NOT hallucinate or create content.** Only organize and format existing details. The Notion page acts as the definitive Source of Truth.
7. Move the local scratchpad file (`.md`) to the `market research` subfolder in the `Meddash-Product Manager` directory for auditing and reference.
8. Update the `MEDDASH-PRO-MAN-WORKFLOW-CONTEXT-TIMELINE-LOG.md` to record the research completion.
9. Run `/backup-git` to ensure the workspace and logs are securely synced to GitHub.
