#!/usr/bin/env python3
"""
Holiday Updates Monitor

This script checks the modification dates of holiday files in the countries/ and financial/
directories and identifies files that may need updating based on configurable age thresholds.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from github import Auth, Github
    from github.GithubException import GithubException
except ImportError:
    Auth = None  # type: ignore
    Github = None  # type: ignore
    GithubException = None  # type: ignore


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HolidayUpdatesChecker:
    """Check holiday file updates and manage GitHub issues."""

    def __init__(
        self,
        repo_path: str,
        files_path: str = "holidays",
        threshold_days: int = 180,
        github_token: Optional[str] = None,
        dry_run: bool = False,
    ):
        """
        Initialize the freshness checker.

        Args:
            repo_path: Path to the repository root
            files_path: Path to directory containing holiday files to check
            threshold_days: Days threshold for files (default: 180)
            github_token: GitHub token for API access
            dry_run: If True, don't create actual issues
        """
        self.repo_path = Path(repo_path)
        self.files_path = Path(files_path)
        self.threshold_days = threshold_days
        self.dry_run = dry_run

        self.github: Optional[Github] = None
        self.repo: Optional[Any] = None
        if github_token and Github is not None and Auth is not None:
            try:
                auth = Auth.Token(github_token)
                self.github = Github(auth=auth)
                self.repo = self.github.get_repo("vacanza/holidays")
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub client: {e}")
        elif github_token and (Github is None or Auth is None):
            logger.warning("PyGithub not available, GitHub integration disabled")

    def get_file_age_days(self, file_path: Path) -> int:
        """Get file age in days since last modification."""
        try:
            mtime = file_path.stat().st_mtime
            age = datetime.now() - datetime.fromtimestamp(mtime)
            return age.days
        except OSError as e:
            logger.error(f"Error getting file age for {file_path}: {e}")
            return 0

    def extract_name_from_path(self, file_path: Path) -> str:
        """Extract a human-readable name from file path."""
        name = file_path.stem.replace("_", " ").title()
        return name

    def scan_directory(self, directory: Path, threshold_days: int) -> List[Dict]:
        """
        Scan a directory for outdated files.

        Args:
            directory: Directory to scan
            threshold_days: Age threshold in days

        Returns:
            List of dictionaries with file information
        """
        outdated_files: List[Dict] = []

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return outdated_files

        for file_path in directory.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            age_days = self.get_file_age_days(file_path)

            if age_days > threshold_days:
                last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                file_info = {
                    "path": str(file_path.relative_to(self.repo_path)),
                    "name": self.extract_name_from_path(file_path),
                    "age_days": age_days,
                    "last_modified": last_modified.isoformat(),
                    "threshold_days": threshold_days,
                    "directory_type": directory.name,
                }
                outdated_files.append(file_info)
                logger.info(
                    f"Outdated file found: {file_info['path']} ({age_days} days old)"
                )

        return outdated_files

    def check_freshness(self) -> List[Dict]:
        """
        Check freshness of all holiday files.

        Returns:
            List of dictionaries containing outdated files
        """
        logger.info("Starting holiday updates check...")

        files_dir = self.repo_path / self.files_path
        outdated_files = self.scan_directory(files_dir, self.threshold_days)

        logger.info(f"Found {len(outdated_files)} outdated files total")

        return outdated_files

    def create_issue_title(self, file_info: Dict) -> str:
        """Create a GitHub issue title for an outdated file."""
        return f"[Holiday Updates] Update required: {file_info['name']}"

    def create_issue_body(self, file_info: Dict) -> str:
        """Create a GitHub issue body for an outdated file."""
        last_modified = datetime.fromisoformat(file_info["last_modified"])
        formatted_date = last_modified.strftime("%B %d, %Y")

        template_path = Path(__file__).parent / "issue_body_template.md"
        try:
            with open(template_path, encoding="utf-8") as f:
                template = f.read()
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}")
            return f"File {file_info['path']} needs updating (last modified: {formatted_date})"
        return template.format(
            path=file_info["path"],
            formatted_date=formatted_date,
            age_days=file_info["age_days"],
            threshold_days=file_info["threshold_days"],
            directory_type=file_info["directory_type"].title(),
            name=file_info["name"],
            overdue_days=file_info["age_days"] - file_info["threshold_days"],
        )

    def find_existing_issue(self, file_info: Dict) -> Optional[Any]:
        """Find existing open issue for a file."""
        if not self.repo:
            return None

        try:
            title = self.create_issue_title(file_info)
            issues = self.repo.get_issues(state="open")

            for issue in issues:
                if issue.title == title:
                    return issue
        except GithubException as e:
            logger.error(f"Error searching for existing issues: {e}")

        return None

    def create_github_issue(self, file_info: Dict) -> bool:
        """Create a GitHub issue for an outdated file."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create issue for: {file_info['path']}")
            return True

        if not self.repo:
            logger.error("GitHub repository not available")
            return False

        existing_issue = self.find_existing_issue(file_info)
        if existing_issue:
            logger.info(
                f"Existing issue found for {file_info['path']}: #{existing_issue.number}"
            )
            return True

        try:
            title = self.create_issue_title(file_info)
            body = self.create_issue_body(file_info)
            labels = ["holiday-updates", "maintenance", "data-update"]

            issue = self.repo.create_issue(title=title, body=body, labels=labels)

            logger.info(f"Created issue #{issue.number} for {file_info['path']}")
            return True

        except GithubException as e:
            logger.error(f"Failed to create issue for {file_info['path']}: {e}")
            return False

    def process_outdated_files(self, outdated_files: List[Dict]) -> Dict[str, int]:
        """
        Process outdated files and create GitHub issues.

        Returns:
            Dictionary with counts of issues created/updated
        """
        stats = {"created": 0, "skipped": 0, "errors": 0}

        for file_info in outdated_files:
            try:
                if self.create_github_issue(file_info):
                    stats["created"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error processing {file_info['path']}: {e}")
                stats["errors"] += 1

        return stats

    def run(self) -> Dict:
        """Run the complete freshness check and issue creation process."""
        logger.info("Starting holiday updates monitoring...")

        outdated_files = self.check_freshness()

        stats = self.process_outdated_files(outdated_files)

        logger.info("Updates check completed:")
        logger.info(f"  - Issues created: {stats['created']}")
        logger.info(f"  - Errors: {stats['errors']}")

        self._set_github_outputs(outdated_files, stats)

        return {
            "outdated_files": outdated_files,
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
        }

    def _set_github_outputs(self, outdated_files: List[Dict], stats: Dict) -> None:
        """Set GitHub Actions output variables."""
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.getenv("GITHUB_OUTPUT"), "a") as f:
                files_json = json.dumps([f["path"] for f in outdated_files])
                f.write(f"outdated_files={files_json}\n")
                f.write(f"outdated_files_count={len(outdated_files)}\n")
                f.write(f"issues_created={stats['created']}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check holiday file updates")
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to repository root (default: current directory)",
    )
    parser.add_argument(
        "--files-path",
        default="holidays",
        help="Path to directory containing holiday files to check (default: holidays)",
    )
    parser.add_argument(
        "--threshold-days",
        type=int,
        default=180,
        help="Age threshold for files in days (default: 180)",
    )
    parser.add_argument("--github-token", help="GitHub token for API access")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't create actual issues, just log what would be done",
    )
    parser.add_argument("--output", help="Output file for results (JSON format)")

    args = parser.parse_args()

    github_token = args.github_token or os.getenv("GITHUB_TOKEN")

    checker = HolidayUpdatesChecker(
        repo_path=args.repo_path,
        files_path=args.files_path,
        threshold_days=args.threshold_days,
        github_token=github_token,
        dry_run=args.dry_run,
    )

    try:
        result = checker.run()

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {args.output}")

        if result["stats"]["errors"] > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
