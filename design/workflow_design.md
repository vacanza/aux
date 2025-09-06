# GitHub Workflow for Fetching Holidays Package Download Data

## Overview
This design document outlines the implementation of a GitHub Actions workflow that automatically fetches daily download statistics for the `holidays` Python package from the pepy.tech API and stores the data in a YAML file.

## Requirements
- Fetch data from `https://api.pepy.tech/service-api/v1/pro/projects/holidays/downloads`
- Extract total downloads for the previous complete month
- Store data in `badges/downloads/monthly.yaml`
- Run daily via GitHub Actions
- Use Python for data fetching and processing

## Architecture

### Components
1. **GitHub Actions Workflow** (`.github/workflows/fetch-downloads.yaml`)
   - Scheduled to run daily at 2:00 AM UTC
   - Uses Python environment
   - Commits changes back to repository

2. **Python Script** (`scripts/fetch_downloads.py`)
   - Makes API request to pepy.tech
   - Processes response data
   - Generates YAML output
   - Handles errors gracefully

3. **Output Structure** (`badges/downloads/monthly.yaml`)
   - Contains timestamp of data fetch
   - Stores monthly download count
   - Includes metadata for tracking

### Data Flow
1. GitHub Actions triggers daily workflow
2. Python script fetches data from pepy.tech API
3. Script processes response and extracts previous month downloads only
4. Data is formatted and written to YAML file with reporting period metadata
5. Changes are committed and pushed to repository

## Implementation Details

### API Endpoint
- URL: `https://api.pepy.tech/api/v2/projects/holidays`
- Method: GET
- Authentication: X-API-Key header
- Response: JSON containing download statistics with enhanced metadata
- Schema includes total_downloads, versions, and daily download data

### YAML Output Format
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

### Error Handling
- Network request failures
- API response parsing errors
- Invalid data format
- File write permissions

### Security Considerations
- No sensitive data involved
- Public API endpoint
- Read-only operations on external data

## Testing Strategy
- Test API connectivity
- Validate YAML output format
- Verify error handling scenarios
- Test workflow execution locally

## Maintenance
- Monitor API endpoint availability
- Track workflow execution success/failure
- Update dependencies as needed
- Review and adjust schedule if necessary
