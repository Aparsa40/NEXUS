# Security Policy

NEXUS connects Discord, OpenRouter, GitHub, and a local SQLite activity store.
It processes project messages and repository metadata, so its runtime and
credentials must be treated as security-sensitive.

## Reporting a vulnerability

Do not publish exploitable vulnerability details, credentials, or personal
data in a public issue.

If GitHub Private Vulnerability Reporting is enabled, use the repository's
Security tab. Otherwise, contact the maintainer privately through their
GitHub profile. Include impact and reproduction steps, and redact all live
tokens from reports, logs, and screenshots.

## Credential handling

- Store Discord, GitHub, and OpenRouter credentials in environment variables.
- Keep .env out of version control; .env_example must contain placeholders.
- Use a fine-grained GitHub token scoped to the target repository.
- Grant only read access to Metadata, Contents, Pull requests, Issues, and
  Actions for the current coordinator.
- Do not grant GitHub write permissions unless a separately reviewed feature
  explicitly requires them.
- Rotate credentials immediately if exposed or suspected to be compromised.
- Never log authorization headers, API keys, or bot tokens.

## Discord channel and agent trust

- Configure NEXUS_CHANNEL_IDS with only the channels where NEXUS should
  answer human requests.
- Configure NEXUS_AGENT_CHANNEL_IDS with channels containing trusted agent
  activity. Do not use broad public channels.
- Set NEXUS_AGENT_BOT_IDS when only specific Discord bot identities should
  be observed.
- Messages from agents are untrusted input. They may contain inaccurate
  claims, prompt-injection attempts, or malicious links.
- Do not post secrets, access tokens, private keys, or personal data in
  monitored channels.

## Data retention and model processing

- Activity messages are stored in a local SQLite database.
- Configure NEXUS_ACTIVITY_RETENTION_DAYS to limit retention.
- The database path should be on a protected disk and is excluded from Git.
- Selected recent Discord activity and GitHub metadata are sent to OpenRouter
  as model context. Review the provider's data handling terms before using
  private repositories or sensitive project discussions.
- Restrict access to the machine, environment file, and database.

## Current security boundaries

- The coordinator's GitHub integration is read-only. It does not edit files,
  create commits, create issues, create pull requests, or merge changes.
- It does not authenticate an agent's claimed identity beyond the Discord
  account/bot identity attached to a message.
- It does not independently verify that an agent actually ran a test or used a
  particular tool; such statements are recorded as claims unless corroborated
  by GitHub evidence.
- A project report based on metadata and chat history is not a source-code
  security audit.

## Recommended repository protections

The repository owner should configure GitHub settings separately:

1. Protect main and require pull requests.
2. Require the relevant Actions checks before merging.
3. Require maintainer review.
4. Restrict direct pushes and disable force pushes.
5. Review token permissions and repository access periodically.

These controls are enforced by GitHub settings, not by this bot or this file.
