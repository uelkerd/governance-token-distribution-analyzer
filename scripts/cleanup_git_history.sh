#!/bin/bash
# Script to clean up historical data files from Git tracking

# Ensure we're in the project root
cd "$(git rev-parse --show-toplevel)"

# Remove historical data files from Git tracking but keep locally
git rm --cached -r data/historical/ 2>/dev/null || true
git rm --cached data/*_analysis_*.json 2>/dev/null || true
git rm --cached data/proposal_validation_*.json 2>/dev/null || true

echo "Historical data files are now untracked. They still exist locally but won't be committed."
echo "To verify, run 'git status' and check that the files are no longer listed as tracked."
echo ""
echo "NOTE: If you need to commit changes to these files in the future,"
echo "you may need to modify the .gitignore file and use 'git add -f' to force-add them." 