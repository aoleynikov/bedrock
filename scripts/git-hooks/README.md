# Git hooks

Optional hooks for this repo.

## commit-msg: strip trailers

Removes `Co-authored-by:`, `Signed-off-by:`, and similar trailers from every commit message. Useful if your editor (e.g. Cursor) adds them and has no setting to disable it.

**Install (one-time):**

```bash
cp scripts/git-hooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

After that, all commits (from the IDE or CLI) will have those trailer lines removed before the commit is recorded.
