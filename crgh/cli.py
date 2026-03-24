"""CLI entry point for crgh."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
from perceval.backends.core.github import GitHub
from perceval.archive import Archive

from crgh.github_api import count_issues_and_prs, list_public_repos


@click.group()
def main():
    """CHAOSS Report for GitHub Organizations."""


@main.command("repo-stats")
@click.argument("org")
@click.option("--token", envvar="GITHUB_TOKEN", required=True, help="GitHub API token.")
def repo_stats(org: str, token: str):
    """List public repos for ORG with issue and pull-request counts."""
    try:
        repos = list_public_repos(org, token)
    except Exception as exc:
        click.echo(f"Error fetching repos: {exc}", err=True)
        sys.exit(1)

    repositories = []
    for name in repos:
        click.echo(f"Counting {org}/{name} ...", err=True)
        try:
            issues, prs = count_issues_and_prs(org, name, token)
        except Exception as exc:
            click.echo(f"  Warning: could not count {name}: {exc}", err=True)
            issues, prs = 0, 0
        repositories.append({"name": name, "issues": issues, "pull-requests": prs})

    result = {"org": org, "repositories": repositories}
    click.echo(json.dumps(result, indent=2))


@main.command("gather-stats")
@click.argument("repo_info_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--output-dir", required=True, help="Directory to write output files.")
@click.option("--since", required=True, help="Fetch items on or after this date (YYYY-MM-DD).")
@click.option("--token", envvar="GITHUB_TOKEN", required=True, help="GitHub API token.")
def gather_stats(repo_info_file: str, output_dir: str, since: str, token: str):
    """Fetch detailed issue and PR data for repos listed in REPO_INFO_FILE."""

    try:
        since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        click.echo("Error: --since must be in YYYY-MM-DD format.", err=True)
        sys.exit(1)

    with open(repo_info_file) as f:
        repo_info = json.load(f)

    org = repo_info.get("org")
    if not org:
        click.echo("Error: repo info file is missing the 'org' field.", err=True)
        sys.exit(1)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    archive_path = out_path / ".cache.sqlite"

    if not archive_path.exists():
        archive = Archive.create(archive_path)
    else:
        archive = Archive(archive_path)

    for repo in repo_info.get("repositories", []):
        name = repo["name"]
        click.echo(f"Fetching {org}/{name} since {since} ...", err=True)

        issues = []
        pull_requests = []

        try:
            backend = GitHub(
                owner=org,
                repository=name,
                api_token=[token],
                sleep_for_rate=True,
                sleep_time=60,
                archive=archive
            )

            for item in backend.fetch(from_date=since_dt):
                if "pull_request" in item["data"]:
                    pull_requests.append(item)
                else:
                    issues.append(item)

        except Exception as exc:
            click.echo(f"  Warning: failed to fetch {name}: {exc}", err=True)
            continue

        issues_file = out_path / f"{name}-issues.json"
        prs_file = out_path / f"{name}-pull-requests.json"

        issues_file.write_text(json.dumps(issues, indent=2, default=str))
        prs_file.write_text(json.dumps(pull_requests, indent=2, default=str))

        click.echo(
            f"  Wrote {len(issues)} issues → {issues_file}", err=True
        )
        click.echo(
            f"  Wrote {len(pull_requests)} pull requests → {prs_file}", err=True
        )

    click.echo("Done.", err=True)
