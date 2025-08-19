#!/usr/bin/env python3
"""
Fetch monthly download statistics for the holidays package from pepy.tech API.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

OUTPUT_FILE = Path("badges/downloads/pepy.tech.yaml")
PACKAGE_NAME = "holidays"
API_URL = "https://api.pepy.tech/api/v2/projects/holidays"


def fetch_download_data() -> Optional[Dict[str, Any]]:
    """Fetch download data from pepy.tech API with authentication."""
    try:
        api_key = os.environ.get("PEPY_TECH_API_KEY")
        if not api_key:
            logger.error("PEPY_TECH_API_KEY environment variable not set")
            return None

        logger.info(f"Fetching download data from {API_URL}")

        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

        response = requests.get(API_URL, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched download data")
        return data

    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from API: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return None


def get_previous_month_dates():
    """Get the start and end dates of the previous complete month."""
    now = datetime.now(timezone.utc)
    first_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_previous_month = first_current_month - timedelta(days=1)
    first_previous_month = last_previous_month.replace(day=1)
    return first_previous_month, last_previous_month


def extract_monthly_downloads(data: Dict[str, Any]) -> Optional[int]:
    """Extract download count for the previous complete month only."""
    try:
        logger.info(f"Processing API response with keys: {list(data.keys())}")

        if "downloads" not in data:
            logger.error("No 'downloads' key found in API response")
            return None

        downloads = data["downloads"]
        if not isinstance(downloads, dict):
            logger.error("'downloads' is not a dictionary")
            return None

        first_previous_month, last_previous_month = get_previous_month_dates()
        logger.info(
            f"Calculating downloads for previous month: {first_previous_month.strftime('%Y-%m-%d')} to {last_previous_month.strftime('%Y-%m-%d')}"
        )

        previous_month_downloads = 0
        processed_dates = []

        for date_str, version_data in downloads.items():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                if first_previous_month <= date_obj <= last_previous_month:
                    if isinstance(version_data, dict):
                        daily_total = sum(
                            int(value)
                            for value in version_data.values()
                            if isinstance(value, (int, float))
                        )
                        previous_month_downloads += daily_total
                        processed_dates.append(date_str)
            except ValueError as e:
                logger.warning(f"Could not parse date '{date_str}': {e}")
                continue

        logger.info(f"Processed {len(processed_dates)} days from previous month")
        logger.info(f"Previous month total downloads: {previous_month_downloads}")

        if len(processed_dates) == 0:
            logger.warning("No data found for the previous month")
            return None

        return previous_month_downloads

    except Exception as e:
        logger.error(f"Error extracting monthly downloads: {e}")
        return None


def humanize_number(value: int) -> str:
    """Convert a number to human-readable format with K/M/B suffixes, rounded to full units."""
    if value < 1000:
        return str(value)

    # Round to nearest thousand, million, billion, etc.
    if value < 1000000:
        # Round to nearest thousand
        rounded = round(value / 1000)
        if rounded == 0:
            return "1K"
        # If rounding to 1000K, convert to 1M
        if rounded >= 1000:
            return "1M"
        return f"{rounded}K"
    elif value < 1000000000:
        # Round to nearest million
        rounded = round(value / 1000000)
        if rounded == 0:
            return "1M"
        # If rounding to 1000M, convert to 1B
        if rounded >= 1000:
            return "1B"
        return f"{rounded}M"
    else:
        # Round to nearest billion
        rounded = round(value / 1000000000)
        if rounded == 0:
            return "1B"
        return f"{rounded}B"


def create_output_data(
    monthly_downloads: int, api_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create the output data structure with enhanced information from API v2."""
    first_previous_month, last_previous_month = get_previous_month_dates()

    output_data = {
        "data_source": "pepy.tech_v2",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    # Add most recent data date after last_updated
    if "downloads" in api_data:
        dates = list(api_data["downloads"].keys())
        if dates:
            dates.sort(reverse=True)
            most_recent_date = dates[0]
            output_data["most_recent_data_date"] = most_recent_date

    # Add package and reporting period
    output_data["package"] = PACKAGE_NAME
    output_data["reporting_period"] = {
        "start_date": first_previous_month.strftime("%Y-%m-%d"),
        "end_date": last_previous_month.strftime("%Y-%m-%d"),
    }

    # Group daily downloads values together (raw + human)
    if "downloads" in api_data:
        dates = list(api_data["downloads"].keys())
        if dates:
            dates.sort(reverse=True)
            most_recent_date = dates[0]
            recent_data = api_data["downloads"][most_recent_date]
            if isinstance(recent_data, dict):
                recent_total = sum(
                    int(value)
                    for value in recent_data.values()
                    if isinstance(value, (int, float))
                )
                # Group daily downloads values together
                output_data["daily_downloads"] = recent_total
                output_data["daily_downloads_human"] = humanize_number(recent_total)

    # Group all download values together in one section
    output_data["monthly_downloads"] = monthly_downloads
    output_data["monthly_downloads_human"] = humanize_number(monthly_downloads)

    # Group total downloads values together (raw + human)
    if "total_downloads" in api_data:
        total_downloads = api_data["total_downloads"]
        output_data["total_downloads_all_time"] = total_downloads
        output_data["total_downloads_all_time_human"] = humanize_number(total_downloads)

    return output_data


def save_yaml_data(data: Dict[str, Any]) -> bool:
    """Save data to YAML file."""
    try:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully saved data to {OUTPUT_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save YAML file: {e}")
        return False


def main() -> int:
    """Main function."""
    logger.info("Starting download data fetch process")

    api_data = fetch_download_data()
    if api_data is None:
        logger.error("Failed to fetch data from API")
        return 1

    monthly_downloads = extract_monthly_downloads(api_data)
    if monthly_downloads is None:
        logger.error("Failed to extract monthly downloads from API response")
        return 1

    logger.info(f"Extracted monthly downloads: {monthly_downloads}")

    output_data = create_output_data(monthly_downloads, api_data)

    if not save_yaml_data(output_data):
        logger.error("Failed to save data to YAML file")
        return 1

    logger.info("Download data fetch process completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
