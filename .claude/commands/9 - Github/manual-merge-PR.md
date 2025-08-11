<!--
/**
 * Purpose: Create a PR and manually review/merge it (solo dev).
 * Description: Use PRs to organize work; open PR, self-review, wait for CI (if any), merge (squash), then sync and clean up.
 * Key Actions: push-branch → create-PR → self-review → merge → sync → cleanup.
 */
-->

### Command: Manual Merge a Pull Request (Solo Dev)

<!-- AIDEV-NOTE: Solo dev workflow; open PR page for self-review; no external reviewers. -->
<!-- AIDEV-NOTE: Non-interactive; keep commands deterministic. -->

#### Required Inputs

- **REPO_PATH**: Local path to the repo, e.g., `/Users/you/dev/project`
- **FEATURE_BRANCH**: Branch to merge (defaults to current branch)

#### Optional Inputs

- **BASE_BRANCH**: Default `main`
- **OPEN_WEB**: `true` | `false` (default `true`)
- **DELETE_BRANCH**: `true` | `false` (default `true`)

#### Assumptions

- `gh` CLI is installed and authenticated.
- If branch protections require checks, you will merge only after they pass.

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

3. Create the PR targeting base (ready, not draft)

   ```bash
   gh pr create \
     --base "${BASE_BRANCH:-main}" \
     --head "$CURRENT_BRANCH" \
     --title "feat: ${CURRENT_BRANCH}" \
     --fill
   ```

4. Get PR number and (optionally) open in browser for review

   ```bash
   PR_NUMBER=$(gh pr view --json number -q .number)
   PR_URL=$(gh pr view --json url -q .url)
   echo "PR: $PR_URL"

   if [ "${OPEN_WEB:-true}" = "true" ]; then
     gh pr view "$PR_NUMBER" --web
   fi
   ```

5. **USER INTERVENTION REQUIRED: Review the PR**

   The browser should now be open to your PR. Please:

   - Review the "Files changed" tab to verify your changes
   - Check that CI checks are passing (if any)
   - Ensure commit messages are clear and meaningful
   - Verify the diff matches your intent

   **When ready to merge, continue to the next step.**

6. Merge when ready (squash recommended)

   ```bash
   gh pr merge "$PR_NUMBER" --squash ${DELETE_BRANCH:+--delete-branch}
   ```

7. Sync local base and clean up local branch

   ```bash
   git checkout "${BASE_BRANCH:-main}"
   git pull --rebase origin "${BASE_BRANCH:-main}"

   if [ "${DELETE_BRANCH:-true}" = "true" ]; then
     git branch -d "$CURRENT_BRANCH" || true
   fi
   ```

If there's a git merge conflict, prompt the user to resolve it together.
