# Product specifications index

Table fields:

- Document: Link to document, title is doc name
- Code: path to main code, if feature spec
- Purpose: description of spec and what it does and achieves

| Document | Code | Purpose |
|----------|------|---------|
| [Story Thread Surfacing Slack Bot](story-thread-surfacing-slack-bot.md) | `src/` (TBD) | System for identifying and resurfacing historical Atlantic stories using semantic search, clustering, and Google Trends correlation. Provides on-demand analysis and proactive suggestions via Slack-like interface for journalists. |
| [POC Architecture](poc-architecture.md) | `backend/`, `frontend/` | Implementation architecture for proof-of-concept: Python FastAPI backend with modular service layer, Next.js frontend, Block Kit as universal response format. Includes Infactory API integration with comprehensive logging and flexible environment configuration. |
| [Google Trends Integration](google-trends-integration.md) | `backend/app/integrations/trends.py`, `backend/app/services/trends_watch_service.py`, `backend/app/api/v1/trends.py`, `backend/alembic/` | Real-time Google Trends monitoring using `trendspy` for proactive story discovery. Periodically watches US trends, searches Infactory for relevant Atlantic articles, and surfaces actionable threads with full archive context. Powers proactive feed with scored trend-article matches. **Phases 1, 2, & 3 implemented.** |
| [Shadcn UI Integration](shadcn-ui-integration.md) | `frontend/components/ui/`, `frontend/lib/utils.ts` | Integration of shadcn/ui components with radix-lyra style, Phosphor icons, and stone color scheme. Upgrades Next.js to 16, React to 19, Tailwind to v4, and updates QueryInterface to use shadcn primitives. |
| [Infactory Integration](infactory-integration.md) | `backend/app/integrations/infactory.py` | Atlantic Archive API client with search, article retrieval, and full request/response logging. Supports hybrid/semantic/keyword search modes with configurable parameters. |
| [Environment Configuration](environment-config.md) | `backend/app/config.py`, `.env` | Flexible configuration system that loads `.env` from project root or current directory, supports environment variable overrides, and includes DEBUG logging mode for development. |
| [Trends with Sections and Thresholds](trends-with-sections-and-thresholds.md) | `backend/app/services/trends_watch_service.py`, `backend/app/services/block_formatter.py`, `backend/app/models/schemas.py` | Enhanced trend discovery with section-aware story grouping (Politics, Culture, Technology, etc.) and confidence scoring system. Includes per-story scores and overall message confidence with configurable thresholds for quality filtering. |
| [Pitch Generation](pitch-generation.md) | `backend/app/services/pitch_generator.py`, `backend/app/api/v1/pitches.py` | Generate story pitches using the Infactory answer API based on trend-surfaced articles. Creates comprehensive pitch packages with headline suggestions, historical context, source articles, and follow-up questions. |