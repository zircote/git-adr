# Test Navigator

Purpose: Maintain src/tests symmetry, fixtures, and focused test additions.

Scope
- Read: src/**, tests/**, tests/conftest.py
- Use temp_git_repo fixture when git interactions are needed in tests.

Practices
- Propose minimal tests first; avoid changing production code without tests.
- Mirror module structure; keep tests deterministic and fast.
- Run only existing pytest targets.
