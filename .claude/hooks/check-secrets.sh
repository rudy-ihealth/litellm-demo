#!/bin/bash
# PreToolUse hook: block `git commit` if staged content contains credential-like strings.
# Triggered via .claude/settings.json with `if: "Bash(git commit*)"`.
# Receives Claude Code hook JSON on stdin (we don't need the payload — git provides the diff).

set -uo pipefail

# Bail cleanly outside a git repo.
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  exit 0
fi

# Added lines only (drop file headers).
diff_content=$(git diff --cached -U0 2>/dev/null | grep '^+' | grep -v '^+++' || true)
if [ -z "$diff_content" ]; then
  exit 0
fi

# Strings that mark a line as an obvious placeholder.
placeholder_markers='your-real-key|your[-_]key|replace[-_]me|REPLACE_ME|xxxxxxxx|placeholder|fake[-_]key|example[-_]key|sk-\.\.\.'

# Each entry: human label | extended-regex
patterns=(
  "OpenAI/LiteLLM key|sk-[A-Za-z0-9_-]{20,}"
  "AWS access key id|AKIA[0-9A-Z]{16}"
  "AWS secret access key|aws_secret_access_key[[:space:]]*=[[:space:]]*[A-Za-z0-9/+=]{20,}"
  "GitHub PAT|ghp_[A-Za-z0-9]{20,}"
  "GitHub fine-grained PAT|github_pat_[A-Za-z0-9_]{20,}"
  "Bearer token|[Bb]earer[[:space:]]+[A-Za-z0-9._-]{30,}"
)

found=()

for entry in "${patterns[@]}"; do
  label="${entry%%|*}"
  regex="${entry#*|}"
  matches=$(echo "$diff_content" | grep -inE "$regex" | grep -ivE "$placeholder_markers" || true)
  if [ -n "$matches" ]; then
    found+=("=== ${label} ===")
    found+=("${matches}")
  fi
done

# Dotenv-style: VAR_KEY=value / VAR_TOKEN=value / VAR_SECRET=value / VAR_PASSWORD=value
dotenv_match=$(echo "$diff_content" \
  | grep -iE '^\+[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD)[[:space:]]*=[[:space:]]*[^[:space:]]{8,}' \
  | grep -ivE "$placeholder_markers" \
  | grep -ivE '=[[:space:]]*"?(your[-_]|replace|example|test[-_]?key|dummy|<.*>|\$\{)' \
  || true)
if [ -n "$dotenv_match" ]; then
  found+=("=== dotenv-style assignment ===")
  found+=("${dotenv_match}")
fi

if [ ${#found[@]} -gt 0 ]; then
  {
    echo ""
    echo "BLOCKED: staged changes contain potential credentials."
    echo ""
    for line in "${found[@]}"; do
      echo "${line}"
    done
    echo ""
    echo "Review the matches above. If a match is a placeholder, adjust the regex"
    echo "in .claude/hooks/check-secrets.sh. Otherwise:"
    echo "  git restore --staged <file>      # unstage"
    echo "  # remove the secret, then re-stage and commit"
  } >&2
  exit 2
fi

exit 0
