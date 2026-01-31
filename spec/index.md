# Product specifications index

Table fields:

- Document: Link to document, title is doc name
- Code: path to main code, if feature spec
- Purpose: description of spec and what it does and achieves

| Document | Code | Purpose |
|----------|------|---------|
| [Story Thread Surfacing Slack Bot](story-thread-surfacing-slack-bot.md) | `src/` (TBD) | System for identifying and resurfacing historical Atlantic stories using semantic search, clustering, and Google Trends correlation. Provides on-demand analysis and proactive suggestions via Slack-like interface for journalists. |
| [POC Architecture](poc-architecture.md) | `backend/`, `frontend/` | Implementation architecture for proof-of-concept: Python FastAPI backend with modular service layer, Next.js frontend, Block Kit as universal response format. Designed for future Slack integration while supporting standalone web UI. |