# Test Data Directory

This directory contains generated test data files used by the integration tests.

## Generated Files (Not Tracked in Git)

The following files are automatically generated during test execution:

- `*.json` - JSON data files containing test results
- `*.csv` - CSV data files with tabular test data  
- `*.png` - Generated chart and visualization files

These files are excluded from version control via `.gitignore` as they are:
- Generated automatically during testing
- Can be large in size
- Not needed for repository functionality
- Recreated on each test run

## Purpose

This directory structure is maintained to ensure tests have a consistent location to write temporary data files during execution. 