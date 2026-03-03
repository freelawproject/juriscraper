---
name: juriscraper-release
description: Use this skill to automate a new version release for the juriscraper project. Trigger by asking to "release a new version" or "bump version."
argument-hint: "[patch|minor|major]"
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

# Juriscraper Release Workflow
You are an expert at managing the juriscraper release process. When this skill is active, follow these steps exactly:

1. **Setup**: Ensure local `main` is up-to-date with remote. Pull if necessary.
2. **Version Logic**: Bump the version based on `$ARGUMENTS` (defaults to `patch` if not specified). Examples: if current is `2.1.0`, then `patch` → `2.1.1`, `minor` → `2.2.0`, `major` → `3.0.0`.
3. **Branching**: Create and checkout a new branch named `version-bump-v{version_number}`.
4. **Filesystem Updates**:
   - Update `version` in `pyproject.toml`.
   - Run `uv sync`.
   - **CHANGES.md**: Move the current "Coming up" entries into a new section: `## {version_number} - {YYYY-MM-DD}`. Reset the "Coming up" bullet points to empty:
     ```
     Features:
     -

     Changes:
     -

     Fixes:
     -
     ```
5. **Quality Check**: Run `pre-commit run --all-files`. If it fails, attempt to fix and re-run once.
6. **Git Operations**:
   - Commit all changes as `version bump v{version_number}`.
   - Create a local tag: `v{version_number}`.
7. **Delivery**: Push the branch and open a Pull Request using the GitHub CLI (`gh pr create`). Use the user signature; do not co-author the commits.
8. **Final step for the user**: Print the `git push --tags` command so the user can decide to trigger the final release.

# Constraints
- Do NOT push tags to remote.
- Use `uv` for dependency management.
