# NEXUS — AI Project Coordination Hub

NEXUS is a Discord-based coordination bot for teams of human developers and
independent AI coding agents. It connects Discord, OpenRouter, GitHub, and a
local SQLite activity store.

The bot improves shared project awareness. Coding agents continue to work
directly with their own development tools and GitHub access; NEXUS collects
status, records team updates, identifies blockers, and publishes reports. It is
not a code-writing or GitHub mutation agent.

## Current capabilities

- Natural-language questions and requests in configured Discord channels,
  without requiring the ! prefix.
- Legacy ! commands remain available for compatibility.
- Read-only GitHub visibility: recent commits, branches, open pull requests,
  open issues, and recent GitHub Actions runs.
- Read-only repository file retrieval on request.
- Activity capture from human members and other AI bots in configured agent
  channels. NEXUS records other bots but does not reply to them.
- Persistent activity history in SQLite, with configurable retention.
- On-demand and daily scheduled project reports, delivered to a configured
  Discord channel.
- Reports distinguish confirmed evidence, inferences, missing information,
  blockers, and recommended handoffs.

## Architecture

    Human developers / AI coding agents
                    |
                    v
            Discord project channels
                    |
                    v
              NEXUS coordinator
              /       |        \
             v        v         v
        Message     GitHub    SQLite activity
        routing     reader       history
             \       |         /
              \      v        /
               Coordination analysis
                        |
                 OpenRouter model
                        |
            Replies and scheduled reports

NEXUS does not commit code, edit files, create issues, create pull requests, or
merge changes. GitHub access is read-only in this implementation. The
coordinator reports what it can verify and explicitly identifies unavailable
data. A metadata report is not a substitute for a full source-code audit.

## Technology

- Python 3.10+
- discord.py
- aiohttp
- python-dotenv
- OpenRouter Chat Completions API
- GitHub REST API
- SQLite (Python standard library)

## Requirements

- Python 3.10 or newer.
- A Discord application and bot token.
- A fine-grained GitHub token scoped to the target repository with read-only
  permissions.
- An OpenRouter API key and a model available to your account.
- Discord Message Content Intent enabled in the Developer Portal and in
  the bot code.

Recommended fine-grained GitHub token permissions:

| Permission | Access |
| --- | --- |
| Metadata | Read-only |
| Contents | Read-only |
| Pull requests | Read-only |
| Issues | Read-only |
| Actions | Read-only |

No GitHub write permissions are required by the current coordinator.

## Setup

Clone the repository:

    git clone https://github.com/Aparsa40/NEXUS.git
    cd NEXUS

Create and activate a virtual environment.

Windows PowerShell:

    py -3.10 -m venv .venv
    .\.venv\Scripts\Activate.ps1

macOS / Linux:

    python3 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Copy .env_example to .env and fill in the credentials and Discord channel IDs.
Never commit .env.

PowerShell:

    Copy-Item .env_example .env

macOS / Linux:

    cp .env_example .env

## Configuration

| Variable | Purpose |
| --- | --- |
| DISCORD_TOKEN | Discord bot token. |
| GITHUB_TOKEN | Fine-grained, read-only GitHub token. |
| OPENROUTER_API_KEY | OpenRouter API key. |
| GITHUB_REPO | Target repository in owner/name format. |
| AI_MODEL | OpenRouter model slug, e.g. openrouter/free if available. |
| NEXUS_CHANNEL_IDS | Comma-separated channel IDs where humans may talk to NEXUS. |
| NEXUS_AGENT_CHANNEL_IDS | Channels where messages from other agents are recorded. Defaults to NEXUS_CHANNEL_IDS. |
| NEXUS_AGENT_BOT_IDS | Optional comma-separated bot IDs to observe. Empty means all other bots in agent channels. |
| NEXUS_REPORT_CHANNEL_ID | Destination channel for scheduled reports. Empty disables scheduled reports. |
| NEXUS_REPORT_TIME | Daily report time in 24-hour HH:MM format. Empty disables scheduling. |
| NEXUS_REPORT_TIMEZONE | IANA timezone for the report schedule, e.g. America/New_York. |
| NEXUS_DB_PATH | SQLite activity database path. |
| NEXUS_ACTIVITY_RETENTION_DAYS | Number of days to retain recorded messages. |
| LOG_LEVEL | Logging level; defaults to INFO. |

Copy channel IDs using Discord Developer Mode. Add only channels intended for
project coordination. If NEXUS_CHANNEL_IDS is empty, natural-language
requests and prefix commands are disabled. Keep agent channels limited to
trusted bots; populate NEXUS_AGENT_BOT_IDS for strict filtering.

The bot needs permission to view channels, read message history, send messages,
and use the message content intent. It must be invited to the report channel.

## Using NEXUS

In an allowed channel, ask naturally, for example:

- وضعیت فعلی ریپو را بررسی کن و گزارش بده.
- آخرین Commitها و Branchهای فعال را نشان بده.
- PRهای باز و وضعیت CI را بررسی کن.
- فعالیت DeepSeek و Mistral را خلاصه کن و موانع را بگو.
- برای جلسه بعدی، ریسک‌ها و کارهای باقی‌مانده را جمع‌بندی کن.

Compatibility commands:

| Command | Purpose |
| --- | --- |
| !help | Show help. |
| !ping | Check Discord Gateway latency. |
| !ask prompt | Ask the configured model. |
| !خواندکد path | Read a repository text file. |
| !status / !report | Generate a project report. |
| !branches | List branches. |
| !prs | List open pull requests. |
| !commits | List recent commits. |

## Activity and report behavior

- Human messages in NEXUS_CHANNEL_IDS and NEXUS_AGENT_CHANNEL_IDS are recorded.
  Only NEXUS_CHANNEL_IDS receive natural-language replies and prefix commands.
- Other bot messages are recorded only in NEXUS_AGENT_CHANNEL_IDS; NEXUS does
  not answer those messages, preventing bot-to-bot reply loops.
- Activity is stored locally in SQLite. The database is excluded from Git.
- Scheduled reports are checked every 30 seconds and published once per local
  calendar day at the configured time. The last successful report date is
  persisted to prevent duplicate daily reports.
- If GitHub Actions data or another endpoint is inaccessible, the report must
  disclose that gap rather than treating it as a passing result.

## Privacy and operational limits

- Discord message content in configured agent channels is stored locally for
  the configured retention period. Do not include secrets or personal data in
  agent status messages.
- The optional bot ID allowlist should be used when agent channels may contain
  untrusted bots.
- OpenRouter receives the prompt context needed to answer, including selected
  recent activity and GitHub metadata. Review the provider's data policies
  before using private project information.
- The bot does not currently provide cross-server identity verification,
  cryptographic agent attestations, or a full audit trail of agent tool calls.
- Natural-language routing uses lightweight intent detection; it is not yet a
  fully general tool-calling agent.

## Quality checks

Run locally:

    python -m compileall -q bot.py nexus_core.py tests
    python -m unittest discover -s tests -v
    python -m pip install ruff
    ruff check .
    npx --yes markdownlint-cli2 "**/*.md"

GitHub Actions runs compilation, unit tests, Ruff, dependency checks, and
Markdown linting on pull requests. A TypeScript check runs only if TypeScript
source files and tsconfig.json are added; this repository is currently
Python-only.

## Contributing and security

Read CONTRIBUTING.md and SECURITY.md.

## License

MIT. See LICENSE.
