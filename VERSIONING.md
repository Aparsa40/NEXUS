# Versioning Policy

NEXUS intends to use [Semantic Versioning 2.0.0](https://semver.org/) for published releases. A release version has the form `MAJOR.MINOR.PATCH`:

- **MAJOR** — incompatible changes to documented commands, configuration, integrations, or public behavior.
- **MINOR** — backward-compatible functionality additions.
- **PATCH** — backward-compatible bug fixes and security fixes.

## Pre-1.0 development

Until the first stable `1.0.0` release, use `0.MINOR.PATCH` development versions:

- Increment MINOR for new capabilities or planned feature-level changes.
- Increment PATCH for backward-compatible fixes and maintenance.

Documentation-only changes do not automatically require a release or version increment. Increment a version only when preparing an actual tagged release.

## Release process

1. Update the changelog with user-visible changes.
2. Verify relevant CI checks.
3. Review configuration and dependency changes.
4. Create a tag such as `v0.1.0`.
5. Publish release notes with changes and known limitations.

The repository does not currently declare a released application version. Do not infer one from a development tool or configuration file.
