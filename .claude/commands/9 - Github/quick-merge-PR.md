<!--
/**
 * Purpose: Quick-create and immediately merge a PR (solo dev, no review).
 * Description: For simple changes—create PR, squash-merge right away, then sync local main and clean up branches.
 * Key Actions: push-branch → create-PR → immediate-merge → sync → cleanup.
 */
-->

### Command: Quick Merge a Pull Request (Solo Dev, No Review)

<!-- AIDEV-NOTE: Solo dev; no review; do not open browser; merge immediately after PR creation. -->
<!-- AIDEV-NOTE: Non-interactive; fail fast on errors; keep output concise. -->

#### Required Inputs

- **REPO_PATH**: Local path to the repo, e.g., `/Users/you/dev/project`
- **FEATURE_BRANCH**: Branch to merge (defaults to current branch)

#### Optional Inputs

- **BASE_BRANCH**: Default `main`
- **DELETE_BRANCH**: `true` | `false` (default `true`)

#### Assumptions

- `gh` CLI is installed and authenticated.
- Branch protection does not require checks/reviews before merge. If it does, use the manual merge flow instead.

---

### Steps

1. Navigate to repo and resolve branch

```bash
cd "${REPO_PATH}"
CURRENT_BRANCH="${FEATURE_BRANCH:-$(git branch --show-current)}"
echo "Current branch: $CURRENT_BRANCH"
```

2. Push branch to remote (set upstream if first push)

```bash
git push -u origin "$CURRENT_BRANCH"
```

3. Create the PR targeting base

```bash
gh pr create \
  --base "${BASE_BRANCH:-main}" \
  --head "$CURRENT_BRANCH" \
  --title "feat: ${CURRENT_BRANCH}" \
  --fill
```

4. Fetch PR number and merge immediately (squash)

```bash
PR_NUMBER=$(gh pr view --json number -q .number)
if [ -z "$PR_NUMBER" ]; then echo "Failed to obtain PR number" >&2; exit 1; fi

gh pr merge "$PR_NUMBER" --squash ${DELETE_BRANCH:+--delete-branch}
```

5. Sync local base and clean up local branch

```bash
git checkout "${BASE_BRANCH:-main}"
git pull --rebase origin "${BASE_BRANCH:-main}"

if [ "${DELETE_BRANCH:-true}" = "true" ]; then
  git branch -d "$CURRENT_BRANCH" || true
fi
```

---

If there's a git merge conflict, prompt the user to resolve it together. 

