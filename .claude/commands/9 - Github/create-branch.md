<!--
/**
 * Purpose: Prepare a clean feature branch (pre-work only).
 * Description: Syncs the base branch and creates a new feature branch, stopping before any commits, pushes, or PRs.
 * Key Actions: navigate → sync-base → create-branch.
 */
-->

### Command: Prepare a Feature Branch (Pre-Work Only)

<!-- AIDEV-NOTE: Pre-work only. Do NOT commit, push, or open PR in this command. -->
<!-- AIDEV-NOTE: Use non-interactive flags; assume no human input during command execution. -->
<!-- AIDEV-NOTE: Uses git switch (Git 2.23+). Replace with checkout if older Git. -->

#### Required Inputs

- **REPO_PATH**: Local path to the repo, e.g., `/Users/you/dev/project`
- **FEATURE_NAME**: Short-kebab name, e.g., `user-preferences-panel`

#### Optional Inputs

- **BASE_BRANCH**: Default `main`
- **REMOTE_NAME**: Default `origin`

#### Assumptions

- Git is installed; remote points to canonical repository.
- Working tree is clean (no uncommitted changes).

---

### Steps

1. Navigate to repository

   ```bash
   cd "${REPO_PATH}"
   ```

2. Ensure a clean working tree (fail fast if dirty)

   ```bash
   if [ -n "$(git status --porcelain)" ]; then
     echo "Working tree not clean. Commit/stash before preparing branch." >&2
     exit 1
   fi
   ```

3. Sync base branch

   ```bash
   git fetch "${REMOTE_NAME:-origin}"
   git switch "${BASE_BRANCH:-main}"
   git pull --rebase "${REMOTE_NAME:-origin}" "${BASE_BRANCH:-main}"
   ```

4. Create feature branch from latest base

   ```bash
   FEATURE_BRANCH="feat/${FEATURE_NAME}"
   git switch -c "$FEATURE_BRANCH"
   git branch --show-current
   ```

---

#### Naming guidance

- Prefer `feat/<concise-kebab-name>` or `feat/<ticket-id>-<scope>`, e.g., `feat/abc-123-user-preferences-panel`.

<!-- AIDEV-NOTE: Stop here. Next actions (commits, push, PR) are intentionally out of scope. -->
