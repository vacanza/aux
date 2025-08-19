# Holidays Package Download Tracker

This repository contains a GitHub Actions workflow that automatically fetches monthly download statistics for the `holidays` Python package from the pepy.tech API and stores the data in a YAML file.

## Overview

The system consists of:
- A Python script that fetches data from the pepy.tech API
- A GitHub Actions workflow that runs daily
- A YAML file containing the download statistics

## Files

- `scripts/fetch_downloads.py` - Main script to fetch and process download data from pepy.tech API
- `.github/workflows/fetch-downloads.yml` - GitHub Actions workflow for daily data fetching
- `.github/workflows/ci.yml` - CI/CD workflow for testing and quality checks (Python 3.12)
- `tests/test_fetch_downloads.py` - Comprehensive test suite with 97% coverage
- `Makefile` - Development commands and automation
- `requirements.txt` - Python dependencies and development tools
- `pyproject.toml` - Ruff configuration for linting and formatting
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `badges/downloads/monthly.yaml` - Output file (created by the workflow)

## Setup

1. **Clone the repository** (if not already done)
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Development Setup

For contributors and development:

### Quick Setup with Makefile

```bash
# Install development dependencies and setup pre-commit
make install-dev

# See all available commands
make help
```

### Manual Setup

1. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Development Commands

Using the Makefile (recommended):

```bash
# Code quality
make lint          # Run linting checks
make format        # Format code with ruff
make check         # Run all checks (lint + format check)
make quality       # Run lint, format, and tests

# Testing
make test          # Run pytest tests
make test-cov      # Run tests with coverage report
make run           # Run the main script

# Maintenance
make pre-commit    # Run all pre-commit hooks
make clean         # Clean up temporary files
```

Or manually:

```bash
# Check for issues
ruff check scripts/

# Fix issues automatically
ruff check --fix scripts/

# Format code
ruff format scripts/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Testing

The project includes comprehensive test coverage for all functions:

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run the full script (requires API key)
make run
```

### Test Coverage

The test suite covers:
- **Date calculations** - Previous month date range logic
- **API interactions** - Request handling, authentication, error cases
- **Data processing** - Monthly download extraction and validation
- **Output generation** - YAML file creation and metadata
- **Error handling** - Network failures, invalid data, file operations
- **Integration** - Complete workflow from API to output

Current test coverage: **97%**

## Manual Execution

To run the download fetching script manually:

```bash
# Using Makefile
make run

# Or directly
python scripts/fetch_downloads.py
```

This will:
1. Fetch data from the pepy.tech API using the PEPY_TECH_API_KEY
2. Extract download count for the previous complete month only
3. Save the data to `badges/downloads/monthly.yaml`

**Note:** The PEPY_TECH_API_KEY environment variable must be set for the script to work. The script processes only the previous complete month to ensure stable totals.

## GitHub Actions Workflow

The workflow is configured to:
- Run daily at 2:00 AM UTC
- Be manually triggerable via the GitHub Actions tab
- Install Python dependencies
- Execute the fetch script
- Commit and push changes if the data has changed

## Output Format

The YAML file contains:
```yaml
data_source: "pepy.tech_v2"
last_updated: "2024-01-15T10:30:00Z"
monthly_downloads: 12345
most_recent_data_date: "2023-08-29"
most_recent_daily_downloads: 1143552
package: "holidays"
reporting_period:
  end_date: "2024-01-31"
  month: "2024-01"
  start_date: "2024-01-01"
total_downloads_all_time: 1395207458
```

## API Endpoint

The script fetches data from:
`https://api.pepy.tech/api/v2/projects/holidays`

**Authentication:** Requires PEPY_TECH_API_KEY secret to be configured in GitHub repository settings. Uses `X-API-Key` header for authentication.

**API Schema:** Uses the v2 API which provides:
- Total downloads across all versions
- Available package versions
- Daily download counts per version
- Package metadata

## Error Handling

The script includes comprehensive error handling for:
- Missing API key
- Network request failures
- API response parsing errors
- Invalid data format
- File write permissions

## Maintenance

- Monitor the GitHub Actions tab for workflow execution status
- Check the logs if the workflow fails
- Update the API response parsing logic if the endpoint structure changes
- Review and adjust the schedule if needed

## Troubleshooting

If the workflow fails:
1. Check the GitHub Actions logs for error details
2. Verify the API endpoint is accessible
3. Test the script locally to identify issues
4. Update the script if the API response structure has changed
