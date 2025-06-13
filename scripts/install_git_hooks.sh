#!/bin/bash
# Script to install git hooks

# Ensure we're in the project root
cd "$(git rev-parse --show-toplevel)"

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Check for large files (>1MB)
large_files=$(git diff --cached --name-only | xargs -I{} find {} -type f -size +1M 2>/dev/null)
if [ -n "$large_files" ]; then
  echo "ERROR: Attempting to commit the following large files (>1MB):"
  echo "$large_files"
  echo "Please reconsider if these files should be committed."
  echo "To bypass this check, use git commit --no-verify"
  exit 1
fi

# Check for historical data files
historical_files=$(git diff --cached --name-only | grep -E "data/historical/|data/.*_analysis_.*\.json|data/proposal_validation_.*\.json")
if [ -n "$historical_files" ]; then
  echo "WARNING: Attempting to commit historical/generated data files:"
  echo "$historical_files"
  echo "These files should typically NOT be committed."
  echo "If you're sure this is correct, use git commit --no-verify"
  exit 1
fi

# Count the number of lines being changed
lines_changed=$(git diff --cached --numstat | awk '{added += $1; deleted += $2} END {print added + deleted}')
if [ -n "$lines_changed" ] && [ "$lines_changed" -gt 500 ]; then
  echo "WARNING: You are committing $lines_changed lines of code."
  echo "Consider breaking this into smaller, more focused commits."
  echo "To bypass this check, use git commit --no-verify"
  # Exit with warning but allow commit (change to exit 1 to block)
  echo "Press Ctrl+C to cancel or Enter to proceed anyway..."
  read -r
fi

# All checks passed
exit 0
EOF

# Make pre-commit hook executable
chmod +x .git/hooks/pre-commit

# Create pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash

# Get the current branch
current_branch=$(git symbolic-ref --short HEAD)

# Block direct pushes to main
if [ "$current_branch" = "main" ]; then
  echo "ERROR: Direct pushing to main branch is not allowed."
  echo "Please create a feature branch and submit a pull request instead."
  exit 1
fi

# Count total lines being pushed
if git ls-remote --exit-code origin "$current_branch" > /dev/null 2>&1; then
  lines_changed=$(git diff --stat origin/$current_branch | tail -n 1 | cut -d' ' -f5)
else
  echo "WARNING: Remote branch origin/$current_branch does not exist. Skipping line count check."
  lines_changed=0
fi
if [ -n "$lines_changed" ] && [ "$lines_changed" -gt 1000 ]; then
  echo "WARNING: You are pushing $lines_changed lines of code."
  echo "This is a large change that may be difficult to review."
  echo "Consider breaking it into smaller, more focused changes."
  echo "To bypass this check, use git push --no-verify"
  # Exit with warning but allow push (change to exit 1 to block)
  echo "Press Ctrl+C to cancel or Enter to proceed anyway..."
  read -r
fi

# All checks passed
exit 0
EOF

# Make pre-push hook executable
chmod +x .git/hooks/pre-push

echo "Git hooks installed successfully:"
echo "- pre-commit hook: checks for large files and historical data files"
echo "- pre-push hook: prevents direct pushing to main and warns about large changes"
echo ""
echo "To bypass these hooks when needed, use --no-verify flag:"
echo "  git commit --no-verify"
echo "  git push --no-verify" 