# Changelog

Notable user-visible changes are documented here. No formal application
release has been declared; changes remain under Unreleased until a version
is tagged.

## [Unreleased]

### Added

- Discord natural-language request handling and model-assisted intent routing
  in configured project channels.
- Read-only GitHub snapshot collection for commits, branches, PRs, issues, and
  recent Actions runs.
- SQLite-backed activity history for human and AI-agent messages.
- Scheduled daily project reports with configurable channel, local time, and
  timezone.
- Unit tests for message routing, ID parsing, and activity persistence.
- CI execution of Python unit tests.

### Changed

- Reframed NEXUS as a coordination and observability bot, not a coding executor.
- Removed direct GitHub file-writing and confirmation flows from the bot.
- Restricted human interaction and prefix commands to configured Discord
  channels.
- Updated setup and security documentation for read-only GitHub access.

### Security

- GitHub integration uses read-only requests in the coordinator implementation.
- Local SQLite activity data is excluded from version control.
- Agent messages are treated as untrusted context, not executable instructions.

### Limitations

- Natural-language routing uses lightweight intent detection and is not yet a
  fully general tool-calling system.
- Agent identity is based on Discord identity and is not cryptographically
  attested.
- Scheduled reports require explicit channel, time, and timezone configuration.
