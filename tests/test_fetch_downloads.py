"""Tests for fetch_downloads.py script."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

# Import the functions to test
from scripts.fetch_downloads import (
    create_output_data,
    extract_latest_30_days_downloads,
    extract_monthly_downloads,
    fetch_download_data,
    get_latest_30_days_dates,
    get_previous_month_dates,
    humanize_number,
    main,
    save_yaml_data,
)


class TestHumanizeNumber:
    """Test the humanize_number function."""

    def test_humanize_number_small(self):
        """Test humanization of small numbers."""
        assert humanize_number(500) == "500"
        assert humanize_number(999) == "999"

    def test_humanize_number_thousands(self):
        """Test humanization of thousands."""
        assert humanize_number(1000) == "1K"
        assert humanize_number(1500) == "2K"
        assert humanize_number(999999) == "1M"

    def test_humanize_number_millions(self):
        """Test humanization of millions."""
        assert humanize_number(1000000) == "1M"
        assert humanize_number(1500000) == "2M"
        assert humanize_number(999999999) == "1B"

    def test_humanize_number_billions(self):
        """Test humanization of billions."""
        assert humanize_number(1000000000) == "1B"
        assert humanize_number(1500000000) == "2B"
        assert humanize_number(2500000000) == "2B"


class TestGetPreviousMonthDates:
    """Test the get_previous_month_dates function."""

    def test_get_previous_month_dates(self):
        """Test that previous month dates are calculated correctly."""
        with patch("scripts.fetch_downloads.datetime") as mock_datetime:
            # Mock current date to be 2024-02-15
            mock_now = datetime(2024, 2, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now

            first, last = get_previous_month_dates()

            # Should return January 2024 (previous month)
            assert first == datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            assert last == datetime(2024, 1, 31, 0, 0, 0, tzinfo=timezone.utc)

    def test_get_previous_month_dates_year_boundary(self):
        """Test previous month calculation across year boundary."""
        with patch("scripts.fetch_downloads.datetime") as mock_datetime:
            # Mock current date to be 2024-01-15
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now

            first, last = get_previous_month_dates()

            # Should return December 2023
            assert first == datetime(2023, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
            assert last == datetime(2023, 12, 31, 0, 0, 0, tzinfo=timezone.utc)


class TestGetLatest30DaysDates:
    """Test the get_latest_30_days_dates function."""

    def test_get_latest_30_days_dates(self):
        """Test that latest 30 days dates are calculated correctly."""
        with patch("scripts.fetch_downloads.datetime") as mock_datetime:
            # Mock current date to be 2024-02-15
            mock_now = datetime(2024, 2, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now

            start, end = get_latest_30_days_dates()

            # Should return 30 days before 2024-02-15
            assert start == datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc)
            assert end == datetime(2024, 2, 15, 0, 0, 0, tzinfo=timezone.utc)


class TestFetchDownloadData:
    """Test the fetch_download_data function."""

    @patch("scripts.fetch_downloads.requests.get")
    def test_fetch_download_data_success(self, mock_get):
        """Test successful API data fetch."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"downloads": {"2024-01-01": {"1.0": 100}}}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"PEPY_TECH_API_KEY": "test_key"}):
            result = fetch_download_data()

        assert result == {"downloads": {"2024-01-01": {"1.0": 100}}}
        mock_get.assert_called_once()

    @patch("scripts.fetch_downloads.requests.get")
    def test_fetch_download_data_no_api_key(self, mock_get):
        """Test API fetch without API key."""
        result = fetch_download_data()
        assert result is None
        mock_get.assert_not_called()

    @patch("scripts.fetch_downloads.requests.get")
    def test_fetch_download_data_request_exception(self, mock_get):
        """Test API fetch with request exception."""
        from requests import RequestException

        mock_get.side_effect = RequestException("Network error")

        with patch.dict(os.environ, {"PEPY_TECH_API_KEY": "test_key"}):
            result = fetch_download_data()

        assert result is None

    @patch("scripts.fetch_downloads.requests.get")
    def test_fetch_download_data_json_decode_error(self, mock_get):
        """Test API fetch with JSON decode error."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"PEPY_TECH_API_KEY": "test_key"}):
            result = fetch_download_data()

        assert result is None


class TestExtractMonthlyDownloads:
    """Test the extract_monthly_downloads function."""

    def test_extract_monthly_downloads_success(self):
        """Test successful monthly downloads extraction."""
        with patch("scripts.fetch_downloads.get_previous_month_dates") as mock_dates:
            mock_dates.return_value = (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 31, tzinfo=timezone.utc),
            )

            api_data = {
                "downloads": {
                    "2024-01-15": {"1.0": 100, "1.1": 50},
                    "2024-01-16": {"1.0": 200, "1.1": 75},
                    "2024-02-01": {"1.0": 300},  # Should be ignored (current month)
                }
            }

            result = extract_monthly_downloads(api_data)
            assert result == 425  # 100+50+200+75

    def test_extract_monthly_downloads_no_downloads_key(self):
        """Test extraction with missing downloads key."""
        api_data = {"total_downloads": 1000}
        result = extract_monthly_downloads(api_data)
        assert result is None

    def test_extract_monthly_downloads_invalid_downloads_type(self):
        """Test extraction with invalid downloads type."""
        api_data = {"downloads": "not_a_dict"}
        result = extract_monthly_downloads(api_data)
        assert result is None

    def test_extract_monthly_downloads_no_data_for_month(self):
        """Test extraction when no data exists for previous month."""
        with patch("scripts.fetch_downloads.get_previous_month_dates") as mock_dates:
            mock_dates.return_value = (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 31, tzinfo=timezone.utc),
            )

            api_data = {
                "downloads": {
                    "2024-02-01": {"1.0": 100},  # Only current month data
                }
            }

            result = extract_monthly_downloads(api_data)
            assert result is None

    def test_extract_monthly_downloads_invalid_date_format(self):
        """Test extraction with invalid date format."""
        with patch("scripts.fetch_downloads.get_previous_month_dates") as mock_dates:
            mock_dates.return_value = (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 31, tzinfo=timezone.utc),
            )

            api_data = {
                "downloads": {
                    "invalid-date": {"1.0": 100},
                    "2024-01-15": {"1.0": 200},
                }
            }

            result = extract_monthly_downloads(api_data)
            assert result == 200  # Only valid date should be processed


class TestExtractLatest30DaysDownloads:
    """Test the extract_latest_30_days_downloads function."""

    def test_extract_latest_30_days_downloads_success(self):
        """Test successful latest 30 days downloads extraction."""
        with patch("scripts.fetch_downloads.get_latest_30_days_dates") as mock_dates:
            mock_dates.return_value = (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 31, tzinfo=timezone.utc),
            )

            api_data = {
                "downloads": {
                    "2024-01-15": {"1.0": 100},
                    "2024-01-16": {"1.0": 200},
                    "2024-02-01": {"1.0": 300},  # Outside range
                }
            }

            result = extract_latest_30_days_downloads(api_data)
            assert result == 300  # 100 + 200

    def test_extract_latest_30_days_downloads_no_downloads_key(self):
        """Test extraction when downloads key is missing."""
        api_data = {"other_key": "value"}
        result = extract_latest_30_days_downloads(api_data)
        assert result is None

    def test_extract_latest_30_days_downloads_invalid_downloads_type(self):
        """Test extraction when downloads is not a dictionary."""
        api_data = {"downloads": "not_a_dict"}
        result = extract_latest_30_days_downloads(api_data)
        assert result is None

    def test_extract_latest_30_days_downloads_no_data_for_period(self):
        """Test extraction when no data exists for the period."""
        with patch("scripts.fetch_downloads.get_latest_30_days_dates") as mock_dates:
            mock_dates.return_value = (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 31, tzinfo=timezone.utc),
            )

            api_data = {
                "downloads": {
                    "2024-02-01": {"1.0": 100},  # Outside range
                }
            }

            result = extract_latest_30_days_downloads(api_data)
            assert result is None

    def test_extract_latest_30_days_downloads_invalid_date_format(self):
        """Test extraction with invalid date format."""
        with patch("scripts.fetch_downloads.get_latest_30_days_dates") as mock_dates:
            mock_dates.return_value = (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 31, tzinfo=timezone.utc),
            )

            api_data = {
                "downloads": {
                    "invalid-date": {"1.0": 100},
                    "2024-01-15": {"1.0": 200},
                }
            }

            result = extract_latest_30_days_downloads(api_data)
            assert result == 200  # Only valid date should be processed


class TestCreateOutputData:
    """Test the create_output_data function."""

    def test_create_output_data_basic(self):
        """Test basic output data creation."""
        with patch("scripts.fetch_downloads.get_previous_month_dates") as mock_dates:
            mock_dates.return_value = (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 31, tzinfo=timezone.utc),
            )

            api_data = {"total_downloads": 1000}
            result = create_output_data(500, 1200, api_data)

            assert result["monthly_downloads"] == 500
            assert result["monthly_downloads_human"] == "500"
            assert result["last_30d_downloads"] == 1200
            assert result["last_30d_downloads_human"] == "1K"
            assert result["source"] == "https://pepy.tech/pepy-api"
            assert result["package"] == "holidays"
            assert result["monthly_reporting_period"]["start_date"] == "2024-01-01"
            assert result["monthly_reporting_period"]["end_date"] == "2024-01-31"
            assert result["total_downloads_all_time"] == 1000
            assert result["total_downloads_all_time_human"] == "1K"

    def test_create_output_data_with_downloads(self):
        """Test output data creation with downloads data."""
        with patch("scripts.fetch_downloads.get_previous_month_dates") as mock_dates:
            mock_dates.return_value = (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 31, tzinfo=timezone.utc),
            )

            api_data = {
                "downloads": {
                    "2024-01-15": {"1.0": 100},
                    "2024-01-16": {"1.0": 200},
                }
            }

            result = create_output_data(300, 800, api_data)

            assert result["most_recent_data_date"] == "2024-01-16"
            assert result["daily_downloads"] == 200
            assert result["daily_downloads_human"] == "200"
            assert result["last_30d_downloads"] == 800
            assert result["last_30d_downloads_human"] == "800"


class TestSaveYamlData:
    """Test the save_yaml_data function."""

    def test_save_yaml_data_success(self, tmp_path):
        """Test successful YAML file save."""
        with patch("scripts.fetch_downloads.OUTPUT_FILE", tmp_path / "test.yaml"):
            data = {"test": "data"}
            result = save_yaml_data(data)

            assert result is True
            assert (tmp_path / "test.yaml").exists()

    def test_save_yaml_data_directory_creation(self, tmp_path):
        """Test that directories are created if they don't exist."""
        with patch(
            "scripts.fetch_downloads.OUTPUT_FILE", tmp_path / "nested" / "test.yaml"
        ):
            data = {"test": "data"}
            result = save_yaml_data(data)

            assert result is True
            assert (tmp_path / "nested" / "test.yaml").exists()

    def test_save_yaml_data_permission_error(self, tmp_path):
        """Test YAML save with permission error."""
        with patch("scripts.fetch_downloads.OUTPUT_FILE", Path("/root/test.yaml")):
            data = {"test": "data"}
            result = save_yaml_data(data)

            assert result is False


class TestMain:
    """Test the main function."""

    @patch("scripts.fetch_downloads.fetch_download_data")
    @patch("scripts.fetch_downloads.extract_monthly_downloads")
    @patch("scripts.fetch_downloads.extract_latest_30_days_downloads")
    @patch("scripts.fetch_downloads.create_output_data")
    @patch("scripts.fetch_downloads.save_yaml_data")
    def test_main_success(
        self, mock_save, mock_create, mock_extract_30d, mock_extract, mock_fetch
    ):
        """Test successful main function execution."""
        mock_fetch.return_value = {"downloads": {"2024-01-01": {"1.0": 100}}}
        mock_extract.return_value = 100
        mock_extract_30d.return_value = 150
        mock_create.return_value = {"monthly_downloads": 100}
        mock_save.return_value = True

        result = main()
        assert result == 0

    @patch("scripts.fetch_downloads.fetch_download_data")
    def test_main_fetch_failure(self, mock_fetch):
        """Test main function with fetch failure."""
        mock_fetch.return_value = None

        result = main()
        assert result == 1

    @patch("scripts.fetch_downloads.fetch_download_data")
    @patch("scripts.fetch_downloads.extract_monthly_downloads")
    def test_main_extract_failure(self, mock_extract, mock_fetch):
        """Test main function with monthly extraction failure."""
        mock_fetch.return_value = {"downloads": {}}
        mock_extract.return_value = None

        result = main()
        assert result == 1

    @patch("scripts.fetch_downloads.fetch_download_data")
    @patch("scripts.fetch_downloads.extract_monthly_downloads")
    @patch("scripts.fetch_downloads.extract_latest_30_days_downloads")
    def test_main_extract_30d_failure(self, mock_extract_30d, mock_extract, mock_fetch):
        """Test main function with 30-day extraction failure."""
        mock_fetch.return_value = {"downloads": {}}
        mock_extract.return_value = 100
        mock_extract_30d.return_value = None

        result = main()
        assert result == 1

    @patch("scripts.fetch_downloads.fetch_download_data")
    @patch("scripts.fetch_downloads.extract_monthly_downloads")
    @patch("scripts.fetch_downloads.extract_latest_30_days_downloads")
    @patch("scripts.fetch_downloads.create_output_data")
    @patch("scripts.fetch_downloads.save_yaml_data")
    def test_main_save_failure(
        self, mock_save, mock_create, mock_extract_30d, mock_extract, mock_fetch
    ):
        """Test main function with save failure."""
        mock_fetch.return_value = {"downloads": {"2024-01-01": {"1.0": 100}}}
        mock_extract.return_value = 100
        mock_extract_30d.return_value = 150
        mock_create.return_value = {"monthly_downloads": 100}
        mock_save.return_value = False

        result = main()
        assert result == 1


class TestIntegration:
    """Integration tests for the complete workflow."""

    @patch("scripts.fetch_downloads.requests.get")
    def test_complete_workflow_success(self, mock_get):
        """Test the complete workflow from API fetch to YAML save."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "total_downloads": 1000,
            "downloads": {
                "2024-01-15": {"1.0": 100, "1.1": 50},
                "2024-01-16": {"1.0": 200, "1.1": 75},
            },
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"PEPY_TECH_API_KEY": "test_key"}):
            with patch(
                "scripts.fetch_downloads.get_previous_month_dates"
            ) as mock_dates:
                mock_dates.return_value = (
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                    datetime(2024, 1, 31, tzinfo=timezone.utc),
                )

                with patch(
                    "scripts.fetch_downloads.get_latest_30_days_dates"
                ) as mock_30d_dates:
                    mock_30d_dates.return_value = (
                        datetime(2024, 1, 1, tzinfo=timezone.utc),
                        datetime(2024, 1, 31, tzinfo=timezone.utc),
                    )

                    with patch(
                        "scripts.fetch_downloads.OUTPUT_FILE",
                        Path("/tmp/test_output.yaml"),
                    ):
                        result = main()

                        assert result == 0
                        # Verify the workflow executed all steps
                        mock_get.assert_called_once()
