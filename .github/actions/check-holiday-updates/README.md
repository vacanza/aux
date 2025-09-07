# Check Holiday Updates Action

A Docker-based GitHub Action that monitors holiday file freshness and creates GitHub issues for outdated files.

## Features

- **Docker-based**: Isolated environment with all dependencies
- **Configurable paths**: Specify custom paths/globs for holiday files (multiline support)
- **Configurable repository**: Create issues in any repository (default: current repository)
- **Flexible thresholds**: Set age thresholds for file freshness
- **Duplicate prevention**: Checks for existing issues before creating new ones
- **Dry run mode**: Test without creating actual issues
- **Comprehensive logging**: Detailed logs for debugging
- **Results output**: Action outputs for integration with other steps
- **Manual triggers**: Support for workflow_dispatch with custom parameters

## Usage

### Basic Usage

```yaml
name: Holiday Freshness Monitor

on:
  schedule:
    - cron: '0 2 1 * *'  # Run monthly
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Run in dry-run mode (no issues created)'
        required: false
        default: true
        type: boolean
      paths:
        description: 'Multiline list of paths/globs to check (one per line, leave empty for default)'
        required: false
        default: ''
        type: string
      repository:
        description: 'Repository where issues will be created (owner/repo)'
        required: false
        default: 'vacanza/holidays'
        type: string
      threshold_days:
        description: 'Age threshold for files in days'
        required: false
        default: '120'
        type: string

jobs:
  check-updates:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      contents: read
    steps:
      - name: Checkout holidays repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Get full commit history
          repository: vacanza/holidays
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Check Holiday Updates
        id: check-updates
        uses: vacanza/aux/.github/actions/check-holiday-updates@main
        with:
          dry_run: ${{ inputs.dry_run || false }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          paths: ${{ inputs.paths || 'holidays/countries/*.py' }}
          repository: ${{ inputs.repository || 'vacanza/holidays' }}
          threshold_days: ${{ inputs.threshold_days || '120' }}

      - name: Display results
        run: |
          echo "📊 Holiday Update Check Results:"
          echo "  • Outdated files found: ${{ steps.check-updates.outputs.outdated_files_count }}"
          echo "  • Issues created: ${{ steps.check-updates.outputs.issues_created_count }}"
```

### Advanced Usage with Custom Paths

```yaml
- name: Check Holiday Updates
  uses: vacanza/aux/.github/actions/check-holiday-updates@main
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    paths: |
      holidays/countries/*.py
      holidays/financial/*.py
      custom/holidays/*.py
    repository: myorg/issues-repo
    threshold_days: '90'
    dry_run: 'false'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github_token` | GitHub token for API access | Yes | - |
| `paths` | Multiline list of paths/globs to check for holiday files | Yes | `holidays/countries/*.py` |
| `repository` | Repository where issues will be created (owner/repo) | No | `vacanza/holidays` |
| `threshold_days` | Age threshold for files in days | No | `180` |
| `dry_run` | Dry run mode (no issues created) | No | `false` |

### Paths Input Format

The `paths` input supports multiple formats:

**Multiline (recommended):**

```yaml
paths: |
  holidays/countries/*.py
  holidays/financial/*.py
  custom/holidays/*.py
```

**Single line:**

```yaml
paths: holidays/countries/*w.py
```

**Glob patterns supported:**

- `holidays/countries/*.py` - All Python files in countries directory
- `holidays/**/*.py` - All Python files in holidays subdirectories
- `custom/holidays/specific_file.py` - Specific file

## Outputs

| Output | Description |
|--------|-------------|
| `issues_created_count` | Total number of GitHub issues created |
| `outdated_files_count` | Total number of outdated files found |

## GitHub Issues

When outdated files are found, the action creates GitHub issues with:

- **Title**: `Update required: {Country/Market Name}`
- **Body**: File details, age information, and suggested actions
- **Repository**: Configurable (default: current repository)
- **No labels**: Issues are created without automatic labels for flexibility

### Issue Template

```markdown
## Holiday Data Updates Alert

**Path:** `holidays/countries/example.py`
**Last Modified:** January 01, 2023
**Age:** 200 days (threshold: 180 days)

This holiday data file hasn't been updated recently and may need verification.

### Suggested Actions

- [ ] Verify current holiday data accuracy
- [ ] Check for new holidays or changes in Example Country
- [ ] Update file if necessary
- [ ] Close this issue when complete

---
This issue was automatically created by the Check Holiday Updates Action.
```

## Requirements

- **Permissions**: `issues: write`, `contents: read`
- **Docker**: Action runs in an Alpine Linux container with Python 3.13
- **Dependencies**: PyGithub, python-dateutil
- **Git**: Full commit history required for accurate file age calculation

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
  check-holiday-updates \
  --dry-run true \
  --paths "holidays/countries/*.py" \
  --github-token your_token \
  --repository "owner/repo" \
  --threshold-days 180

# Test with actual repository
docker run --rm \
  -v /path/to/repo:/github/workspace \
  check-holiday-updates \
  --dry-run false \
  --paths "holidays/countries/*.py" \
  --github-token your_token \
  --repository "owner/repo" \
  --threshold-days 120
```

### Command Line Arguments

The action supports the following command-line arguments:

- `--dry-run`: Run in dry-run mode (no issues created)
- `--paths`: Multiline list of paths/globs to check
- `--github-token`: GitHub token for API access
- `--repository`: Repository where issues will be created (owner/repo)
- `--threshold-days`: Age threshold for files in days

### Dependencies

The action uses the following Python packages:

- `PyGithub==2.8.1` - GitHub API client
- `python-dateutil==2.9.0` - Date handling utilities

## Examples

### Check Multiple Directories

```yaml
- name: Check All Holiday Files
  uses: vacanza/aux/.github/actions/check-holiday-updates@main
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    paths: |
      holidays/countries/*.py
      holidays/financial/*.py
      holidays/provincial/*.py
    threshold_days: '90'
```

### Create Issues in Different Repository

```yaml
- name: Check Holiday Updates
  uses: vacanza/aux/.github/actions/check-holiday-updates@main
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    repository: myorg/maintenance-issues
    paths: holidays/countries/*.py
    threshold_days: '60'
```

### Manual Workflow with Custom Parameters

When using `workflow_dispatch`, you can customize all parameters:

- **Dry Run**: Test without creating issues
- **Custom Paths**: Specify different files to check
- **Custom Repository**: Create issues in a different repository
- **Custom Threshold**: Set different age thresholds

## License

This action is part of the Vacanza organization and follows the same licensing terms.
