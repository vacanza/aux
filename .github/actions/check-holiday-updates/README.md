# Check Holiday Updates Action

A Docker-based GitHub Action that monitors holiday file updates and creates GitHub issues for outdated files.

## Features

- **Docker-based**: Isolated environment with all dependencies
- **Configurable paths**: Specify custom paths for countries and financial directories
- **Flexible thresholds**: Set different age thresholds for different file types
- **Duplicate prevention**: Checks for existing issues before creating new ones
- **Dry run mode**: Test without creating actual issues
- **Comprehensive logging**: Detailed logs for debugging
- **Results output**: JSON results and action outputs

## Usage

```yaml
name: Holiday Freshness Monitor

on:
  schedule:
    - cron: '0 2 1 * *'  # Run monthly
  workflow_dispatch:

jobs:
  check-freshness:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      contents: read
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Check Holiday Updates
        uses: vacanza/aux/.github/actions/check-holiday-updates@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          countries_path: 'holidays/countries'
          financial_path: 'holidays/financial'
          country_threshold_days: '180'
          financial_threshold_days: '365'
          dry_run: 'false'

      - name: Display results
        run: |
          echo "Outdated countries: ${{ steps.check-freshness.outputs.outdated_countries }}"
          echo "Outdated financial: ${{ steps.check-freshness.outputs.outdated_financial }}"
          echo "Total outdated: ${{ steps.check-freshness.outputs.total_outdated }}"
          echo "Issues created: ${{ steps.check-freshness.outputs.issues_created }}"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github_token` | GitHub token for API access | Yes | - |
| `countries_path` | Path to countries directory relative to repo root | No | `holidays/countries` |
| `financial_path` | Path to financial directory relative to repo root | No | `holidays/financial` |
| `country_threshold_days` | Age threshold for country files in days | No | `180` |
| `financial_threshold_days` | Age threshold for financial files in days | No | `365` |
| `dry_run` | Dry run mode (no issues created) | No | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `outdated_countries` | Number of outdated country files found |
| `outdated_financial` | Number of outdated financial files found |
| `total_outdated` | Total number of outdated files found |
| `issues_created` | Number of GitHub issues created |

## Requirements

- **Permissions**: `issues: write`, `contents: read`
- **Docker**: Action runs in a Python 3.13 container
- **Dependencies**: PyGithub, python-dateutil

## GitHub Issues

When outdated files are found, the action creates GitHub issues with:

- **Title**: `[Holiday Updates] Update required: {Country/Market Name}`
- **Labels**: `holiday-updates`, `maintenance`, `data-update`
- **Body**: File details, age information, and suggested actions

## Development

### Building the Docker Image

```bash
cd .github/actions/check-holiday-updates
docker build -t check-holiday-updates .
```

### Testing Locally

```bash
# Test with dry run
docker run --rm \
  -v /path/to/repo:/github/workspace \
  -e GITHUB_TOKEN=your_token \
  check-holiday-updates \
  --dry-run

# Test with actual repository
docker run --rm \
  -v /path/to/repo:/github/workspace \
  -e GITHUB_TOKEN=your_token \
  check-holiday-updates
```

### Dependencies

The action uses the following Python packages:
- `PyGithub==2.8.1` - GitHub API client
- `python-dateutil==2.9.0` - Date handling utilities

## License

This action is part of the Vacanza organization and follows the same licensing terms.
