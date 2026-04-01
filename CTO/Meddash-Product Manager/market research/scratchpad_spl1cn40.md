# Novita AI API Research

## Task
- Search for Novita AI API authentication header.
- Search for Novita AI model list endpoint.
- Confirm authentication method (`Authorization: Bearer` or other).
- Find the correct base URL.

## Progress
- [x] Research authentication header
- [x] Research model list endpoint
- [x] Confirm base URL
- [x] Summarize findings

## Findings
- **Authentication Header**: `Authorization: Bearer <API Key>` (Confirmed in official documentation).
- **Base URL**: `https://api.novita.ai/openai` (Recommended in documentation for OpenAI compatibility).
- **Model List Endpoint**: `https://api.novita.ai/openai/v1/models` (Standard OpenAI convention, confirmed via documentation redirects).
- **Note on v3**: Although ChatGPT advice mentioned `v3`, official documentation uses the paths without `v3`. It's safer to use the documented `https://api.novita.ai/openai` base path.
