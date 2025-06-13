# Git Best Practices for Governance Token Distribution Analyzer

## Key Principles

1. **Keep PRs Small and Focused**
   - Target less than 400-500 lines of changes per PR
   - Focus on a single feature, bug fix, or improvement
   - Split large changes into multiple logical PRs

2. **Avoid Committing Generated Files**
   - Always check what you're committing with `git status` before making a commit
   - Use `.gitignore` to exclude generated data files
   - When in doubt, stage files individually rather than using `git add .`

3. **Work on Feature Branches**
   - Never make changes directly on `main`
   - Create descriptive branch names: `feature/name`, `bugfix/name`, `refactor/name`
   - Pull from `main` frequently to avoid large merge conflicts

## Common Pitfalls to Avoid

### Large PRs
- Problem: Large PRs are difficult to review, prone to issues, and more likely to cause merge conflicts
- Prevention: Break work into smaller, logical chunks and create multiple PRs
- Fix: If a PR becomes too large, consider closing it and creating smaller ones

### Committing Generated Files
- Problem: Generated files create noise in the repository and bloat its size
- Prevention: Keep `.gitignore` updated as new generated file types appear
- Fix: Use `git rm --cached <file>` to remove files from tracking without deleting them

### Force Pushing
- Problem: Force pushing can overwrite history and cause issues for collaborators
- Prevention: Only force push to your own feature branches before they're merged
- Fix: When needed, communicate with the team before force pushing

## Workflow Recommendations

1. **Start of Day**
   ```bash
   git checkout main
   git pull
   git checkout -b feature/my-new-feature
   ```

2. **During Development**
   ```bash
   # Commit small changes frequently
   git add <specific-files>
   git commit -m "[Component] Brief description"
   
   # Stay in sync with main
   git checkout main
   git pull
   git checkout feature/my-new-feature
   git merge main
   ```

3. **Before Creating a PR**
   ```bash
   # Check status and diff
   git status
   git diff --stat
   
   # Review what you're about to commit
   git add <specific-files>
   git diff --cached
   
   # Commit with a clear message
   git commit -m "[Component] Concise description of changes"
   ```

## Tools to Help

1. **Git Hooks**
   - Use pre-commit hooks to prevent committing large files or files matching patterns in `.gitignore`
   - Consider adding hooks to run linters and tests before pushing

2. **Git Config**
   - Set up your git identity:
     ```bash
     git config --global user.name "Your Name"
     git config --global user.email "your.email@example.com"
     ```

3. **Git Aliases**
   - Create helpful aliases for common commands:
     ```bash
     git config --global alias.st status
     git config --global alias.co checkout
     git config --global alias.br branch
     git config --global alias.unstage 'reset HEAD --'
     ```

## Repository-specific Guidelines

1. **Historical Data Files**
   - All files in `data/historical/` should never be committed
   - Files matching `data/*_analysis_*.json` should never be committed
   - Files matching `data/proposal_validation_*.json` should never be committed

2. **Test Generated Files**
   - Never commit test-generated data files
   - Check the test output directories before committing

## Emergency Process for Fixing Large PRs

If you find yourself with an excessively large PR that includes files that shouldn't be committed:

1. Update `.gitignore` to prevent future occurrences
2. Run `scripts/cleanup_git_history.sh` to untrack unwanted files
3. Commit the changes to `.gitignore`
4. Consider splitting the remaining legitimate changes into smaller PRs

Remember: **Smaller PRs = Happier Reviewers = Faster Merges = Better Code** 