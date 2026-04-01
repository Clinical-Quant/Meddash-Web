---
description: Automated sequential market research and reporting workflow.
---

# Automated Market Research Workflow
// turbo-all

1. Use the `browser_subagent` to conduct a comprehensive search on the target competitor or market topic.
2. Research specifically: Product offerings, Data sources, Pricing tiers (Tiers A, B, C), and Customer sentiment.
3. Take screenshots of key product and pricing pages using individual browser steps.
4. Synthesize the findings into a structured markdown report.
5. Append the synthesized report to the specified Notion page using `mcp_notion-mcp-server_API-patch-block-children`.
6. Update the `MEDDASH-PRO-MAN-WORKFLOW-CONTEXT-TIMELINE-LOG.md` to record the research completion.
7. Run `/backup-git` to ensure the workspace and logs are securely synced to GitHub.
