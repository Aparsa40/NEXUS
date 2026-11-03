# Security Policy

NEXUS integrates Discord, OpenRouter, and the GitHub REST API. Its credentials may grant access to private repositories and allow repository contents to be changed. Treat the bot and its runtime environment as security-sensitive.

## Reporting a vulnerability

Do not publish exploitable vulnerability details, credentials, or personal data in a public issue.

If GitHub Private Vulnerability Reporting is enabled, submit a report through the repository's **Security** tab. Otherwise, contact the maintainer privately through their GitHub profile with a description, impact, and reproduction steps. Redact all live tokens from reports, logs, and screenshots.

## Credential handling

- Store Discord, GitHub, and OpenRouter credentials in environment variables.
- Keep `.env` out of version control. The committed `.env_example` must contain placeholders only.
- Use a fine-grained GitHub token scoped to the required repository and minimum permissions.
- Rotate credentials immediately if exposed or suspected to be compromised.
- Never log authorization headers, API keys, or bot tokens.
- Review dependency updates and keep the runtime patched.

## Current implementation limitations

The current bot has important security and governance limitations:

- Confirmed AI file edits are written directly to `main`.
- Pending edit proposals are stored in process memory and lost when the process restarts.
- Users able to invoke edit commands may request repository changes unless access is restricted at the Discord command or channel level.
- A complete branch-per-change, pull-request, and human-approval pipeline is not implemented.

Do not treat this document as evidence that these controls already exist.

## Recommended GitHub protections

The repository owner should configure these controls in GitHub settings:

1. Protect `main` and require pull requests.
2. Require relevant Actions checks before merging.
3. Require maintainer review.
4. Restrict who can push to protected branches.
5. Disable force pushes and branch deletion.
6. Review token permissions and repository access periodically.

Branch protection is enforced by GitHub settings, not this document. Confirm that rules apply to administrators and automation identities where appropriate.

## Supported versions

Security fixes should target the default branch. No separate supported-version policy is defined until formal releases are published.
