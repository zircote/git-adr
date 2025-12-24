# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities in git-adr seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email the maintainers directly at: security@example.com (or use GitHub Security Advisories)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Timeline**: Depends on severity (critical: days, high: 1-2 weeks, medium/low: next release)

### Disclosure Policy

We follow coordinated disclosure:
- We will work with you to understand and address the issue
- We will credit researchers who report valid vulnerabilities (unless you prefer anonymity)
- We request a 90-day disclosure window for fixes

## Security Model

### Design Principles

git-adr is designed as a **local git tool** that:
- Runs with user-level filesystem permissions
- Delegates authentication to git/gh CLI tools
- Stores data in git notes (public metadata, not encrypted)
- Does not run as a network service

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Command injection | All subprocess calls use list arguments (no `shell=True`) |
| Path traversal | Output paths resolved/canonicalized; user controls CLI args |
| File access | Follows user's filesystem permissions (CLI tool, not service) |
| XSS in exports | All user content HTML-escaped in HTML exports |
| YAML/JSON deserialization | Uses safe parsers (frontmatter.loads, yaml.safe_load) |

### Known Limitations

1. **No encryption at rest**: ADRs are stored in git notes without encryption
2. **AI content exposure**: Content sent to configured LLM providers
3. **Wiki sync**: Uses git credentials; ensure proper access controls
4. **Read operations**: Import/attach allow reading from any user-accessible path

### Security Linter Exclusions

The following security rules are intentionally suppressed with justification:

| Rule | Justification |
|------|---------------|
| B404 (subprocess) | This is a git wrapper tool; subprocess is required |
| B603 (subprocess call) | Git commands require subprocess; list args used |
| B607 (partial path) | git should be in PATH; validated at startup |
| S101 (assert) | Tests use assertions |
| S110 (try-except-pass) | Graceful error handling in specific cases |

## Dependency Management

- Dependencies are version-ranged (`>=`) to receive security patches
- `pip-audit` is included in dev dependencies for vulnerability scanning
- Run `uv run pip-audit` to check for known CVEs

## Secure Development Practices

When contributing:
- Never use `shell=True` in subprocess calls
- Always validate output paths against cwd for write operations
- Escape user content in HTML/template outputs
- Use frontmatter/yaml.safe_load for YAML parsing
- Document any security-relevant exceptions in code comments

## Acknowledgments

We thank the security researchers who have helped improve git-adr:

- (Your name could be here)
