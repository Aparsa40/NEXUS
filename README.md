# NEXUS — Discord-Based AI Project Coordination

NEXUS is an early-stage Discord bot for AI-assisted software development coordination. The current Python implementation connects Discord, OpenRouter, and the GitHub REST API.

> **Status:** Initial development. The repository does not yet implement a complete multi-agent orchestration platform, persistent shared memory, or a branch-and-pull-request editing workflow.

## Current capabilities

The implementation in `bot.py` currently supports:
- Discord Gateway connectivity through `discord.py`.
- AI responses through the OpenRouter Chat Completions API.
- GitHub file reading and repository activity summaries.
- AI-assisted file editing with a preview and explicit confirmation.
- Direct bot mentions and prefix commands.

### Discord commands

| Command | Purpose |
| --- | --- |
| `!help` | Show command overview. |
| `!ping` | Check Gateway latency. |
| `!ask <prompt>` | Ask the configured AI model. |
| Mention the bot | Ask a question by mentioning the bot. |
| `!خواندکد <path>` | Read a GitHub repository file. |
| `!status` | Show recent repository activity. |
| `!branches` | List branches. |
| `!prs` | List open pull requests. |
| `!commits` | List recent commits. |
| `!تغییر <path> <instruction>` | Generate and preview a file update. |
| `!تأییدتغییر` | Confirm and write the pending update. |

## Technology

- Python 3.10+
- `discord.py` for Discord
- `aiohttp` for asynchronous HTTP
- `python-dotenv` for environment configuration
- OpenRouter for model inference
- GitHub REST API for repository operations

Dependencies are listed in `requirements.txt`.

## Requirements

- Python 3.10 or newer.
- A Discord application and bot token.
- A GitHub Personal Access Token with the minimum repository permissions needed to read repository metadata and contents and update contents.
- An OpenRouter API key and an available model slug.

Enable **Message Content Intent** in the Discord Developer Portal and in the bot configuration.

## Setup

Clone the repository:

```bash
git clone https://github.com/Aparsa40/NEXUS.git
cd NEXUS
```

Create a virtual environment:

Windows PowerShell:
```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy `.env_example` to `.env` and replace every placeholder. Never commit `.env`.

PowerShell:
```powershell
Copy-Item .env_example .env
```

macOS / Linux:
```bash
cp .env_example .env
```

Required variables:

| Variable | Purpose |
| --- | --- |
| `DISCORD_TOKEN` | Discord bot token. |
| `GITHUB_TOKEN` | GitHub Personal Access Token. |
| `OPENROUTER_API_KEY` | OpenRouter API key. |

Set these project variables explicitly:

| Variable | Purpose |
| --- | --- |
| `GITHUB_REPO` | Target repository as `owner/name`. The current code fallback still points to the legacy `Aparsa40/Rudin-store`; set it to `Aparsa40/NEXUS`. |
| `AI_MODEL` | OpenRouter model slug, for example `openrouter/free` if available to your account. |

Start the bot:
```bash
python bot.py
```

## Important operational notes

- Confirmed `!تأییدتغییر` edits are currently written directly to `main`. The bot does **not** create a feature branch or pull request. Review every proposed update before confirming it.
- GitHub branch protection must be configured separately in repository settings; documentation does not enforce it.
- Pending edit proposals are held in process memory and are lost on restart.
- Treat AI-generated output as untrusted until reviewed.

## Quality checks

GitHub Actions runs Python compilation, Ruff linting, dependency consistency, and Markdown linting. A TypeScript compiler check runs only if TypeScript source files and `tsconfig.json` are added. This repository is currently Python-only, so TypeScript checking is skipped.

Local checks:
```bash
python -m compileall -q bot.py
python -m pip install ruff
ruff check .
npx --yes markdownlint-cli2 "**/*.md"
```

There is not yet an automated application test suite. Add focused unit and integration tests as the bot is separated into testable components.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) before contributing.

## License

MIT. See [LICENSE](LICENSE).
