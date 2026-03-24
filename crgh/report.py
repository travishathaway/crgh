"""Community Activity report generation."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


# ---------------------------------------------------------------------------
# Metric metadata
# ---------------------------------------------------------------------------

METRICS = [
    {
        "id": "contributor-count",
        "title": "Contributor Count",
        "description": (
            "The number of active code commit authors, PR authors, review participants, "
            "issue authors, and issue comment participants over a certain period of time."
        ),
        "objectives": (
            "Open source projects are comprised of a number of different contributors. "
            "Recognizing all contributors to a project is important in knowing who is "
            "helping with such activities as code development, event planning, and "
            "marketing efforts."
        ),
    },
    {
        "id": "updated-issues-count",
        "title": "Updated Issues Count",
        "description": "The number of issues and pull requests updated over a certain period of time.",
        "objectives": "Reveal how many people are actively discussing topics on a repository.",
    },
    {
        "id": "updated-since",
        "title": "Updated Since",
        "description": (
            "The average time (in days) per repository since the repository was last updated. "
            "This is the time between updates to issues and pull requests."
        ),
        "objectives": (
            "This is a slight variation on the updated issue count except that here we focus "
            "on how often the repository is being updated."
        ),
    },
    {
        "id": "code-review-count",
        "title": "Code Review Count",
        "description": "The average number of review comments per pull request created over a certain period of time.",
        "objectives": (
            "To understand the nature of change request review practice within a repository, "
            "and across a collection of repositories. Change Request Reviews can help inform "
            "the quality of the software and the efficiency of development."
        ),
    },
    {
        "id": "issue-comment-frequency",
        "title": "Issue Comment Frequency",
        "description": "The average number of comments per issue created over a certain period of time.",
        "objectives": "See how large discussions on issues are.",
    },
    {
        "id": "pr-comment-frequency",
        "title": "Pull Request Comment Frequency",
        "description": "The average number of comments per pull request created over a certain period of time.",
        "objectives": "See how large discussions on pull requests are.",
    },
    {
        "id": "maintainer-count",
        "title": "Maintainer Count",
        "description": "The average number of maintainers per repository over a certain period of time.",
        "objectives": "To see how many active maintainers are participating for a given repository.",
    },
]

MAINTAINER_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_org_items(data_dir: Path) -> tuple[list[dict], list[dict]]:
    """Load all perceval items from *-issues.json and *-pull-requests.json files."""
    issues: list[dict] = []
    prs: list[dict] = []
    for f in sorted(data_dir.glob("*-issues.json")):
        issues.extend(json.loads(f.read_text()))
    for f in sorted(data_dir.glob("*-pull-requests.json")):
        prs.extend(json.loads(f.read_text()))
    return issues, prs


# ---------------------------------------------------------------------------
# Date / week helpers
# ---------------------------------------------------------------------------

def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _to_week(iso_str: str) -> date:
    """Return the Monday of the week containing the given ISO 8601 date string."""
    dt = _parse_iso(iso_str)
    return (dt - timedelta(days=dt.weekday())).date()


def week_range(since: datetime, until: datetime) -> list[date]:
    """Return an ordered list of week-start (Monday) dates covering [since, until]."""
    # Snap to the Monday of the since-week
    start = (since - timedelta(days=since.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    weeks = []
    current = start
    while current <= until:
        weeks.append(current.date())
        current += timedelta(days=7)
    return weeks


def _item_date(item: dict, field: str = "created_at") -> datetime | None:
    try:
        return _parse_iso(item["data"][field])
    except (KeyError, TypeError, ValueError):
        return None


def _in_range(dt: datetime | None, since: datetime, until: datetime) -> bool:
    return dt is not None and since <= dt <= until


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def metric_contributor_count(
    issues: list[dict], prs: list[dict], weeks: list[str]
) -> pd.Series:
    """Distinct active users per week (authors + commenters on issues and PRs)."""
    week_users: dict[str, set[str]] = {w: set() for w in weeks}

    for item in issues + prs:
        data = item.get("data", {})
        week = _to_week(data.get("created_at", "")) if data.get("created_at") else None
        if week and week in week_users:
            login = (data.get("user") or {}).get("login")
            if login:
                week_users[week].add(login)
            for comment in data.get("comments_data") or []:
                c_login = (comment.get("user") or {}).get("login")
                if c_login:
                    week_users[week].add(c_login)

    return pd.Series({w: len(users) for w, users in week_users.items()}, name="contributor_count")


def metric_updated_issues_count(
    issues: list[dict], prs: list[dict], weeks: list[str]
) -> pd.Series:
    """Count of issues + PRs updated per week."""
    counts: dict[str, int] = {w: 0 for w in weeks}

    for item in issues + prs:
        updated_at = (item.get("data") or {}).get("updated_at")
        if updated_at:
            week = _to_week(updated_at)
            if week in counts:
                counts[week] += 1

    return pd.Series(counts, name="updated_issues_count")


def metric_updated_since(
    issues: list[dict], prs: list[dict], weeks: list[str]
) -> pd.Series:
    """Average days since last update per repo, computed at each week's end."""
    # Build a map: repo -> list of updated_at datetimes
    repo_updates: dict[str, list[datetime]] = {}
    for item in issues + prs:
        sf = item.get("search_fields", {})
        repo = f"{sf.get('owner', '')}/{sf.get('repo', '')}"
        updated_at = (item.get("data") or {}).get("updated_at")
        if updated_at and repo != "/":
            dt = _parse_iso(updated_at)
            repo_updates.setdefault(repo, []).append(dt)

    values: dict[str, float] = {}
    now = datetime.now(tz=timezone.utc)

    for week in weeks:
        week_end = datetime(week.year, week.month, week.day, tzinfo=timezone.utc) + timedelta(days=6, hours=23, minutes=59)
        reference = min(week_end, now)
        days_per_repo = []
        for repo, dts in repo_updates.items():
            past_dts = [d for d in dts if d <= reference]
            if past_dts:
                last = max(past_dts)
                days_per_repo.append((reference - last).total_seconds() / 86400)
        values[week] = sum(days_per_repo) / len(days_per_repo) if days_per_repo else 0.0

    return pd.Series(values, name="updated_since_days")


def metric_code_review_count(prs: list[dict], weeks: list[str]) -> pd.Series:
    """Average comments per PR created per week."""
    comment_sums: dict[str, int] = {w: 0 for w in weeks}
    pr_counts: dict[str, int] = {w: 0 for w in weeks}

    for item in prs:
        data = item.get("data", {})
        created_at = data.get("created_at")
        if not created_at:
            continue
        week = _to_week(created_at)
        if week not in weeks:
            continue
        comment_sums[week] += data.get("comments", 0)
        pr_counts[week] += 1

    return pd.Series(
        {w: (comment_sums[w] / pr_counts[w] if pr_counts[w] else 0.0) for w in weeks},
        name="code_review_count",
    )


def metric_issue_comment_frequency(issues: list[dict], weeks: list[str]) -> pd.Series:
    """Average comments per issue created per week."""
    comment_sums: dict[str, int] = {w: 0 for w in weeks}
    issue_counts: dict[str, int] = {w: 0 for w in weeks}

    for item in issues:
        data = item.get("data", {})
        created_at = data.get("created_at")
        if not created_at:
            continue
        week = _to_week(created_at)
        if week not in weeks:
            continue
        comment_sums[week] += data.get("comments", 0)
        issue_counts[week] += 1

    return pd.Series(
        {w: (comment_sums[w] / issue_counts[w] if issue_counts[w] else 0.0) for w in weeks},
        name="issue_comment_frequency",
    )


def metric_pr_comment_frequency(prs: list[dict], weeks: list[str]) -> pd.Series:
    """Average comments per PR created per week."""
    comment_sums: dict[str, int] = {w: 0 for w in weeks}
    pr_counts: dict[str, int] = {w: 0 for w in weeks}

    for item in prs:
        data = item.get("data", {})
        created_at = data.get("created_at")
        if not created_at:
            continue
        week = _to_week(created_at)
        if week not in weeks:
            continue
        comment_sums[week] += data.get("comments", 0)
        pr_counts[week] += 1

    return pd.Series(
        {w: (comment_sums[w] / pr_counts[w] if pr_counts[w] else 0.0) for w in weeks},
        name="pr_comment_frequency",
    )


def metric_maintainer_count(
    issues: list[dict], prs: list[dict], weeks: list[str]
) -> pd.Series:
    """Average distinct maintainers per repo with activity per week."""
    # week -> repo -> set of maintainer logins
    week_repo_maintainers: dict[str, dict[str, set[str]]] = {
        w: {} for w in weeks
    }

    for item in issues + prs:
        data = item.get("data", {})
        sf = item.get("search_fields", {})
        repo = f"{sf.get('owner', '')}/{sf.get('repo', '')}"
        created_at = data.get("created_at")
        if not created_at or repo == "/":
            continue
        week = _to_week(created_at)
        if week not in weeks:
            continue
        assoc = data.get("author_association", "")
        login = (data.get("user") or {}).get("login")
        if login and assoc in MAINTAINER_ASSOCIATIONS:
            week_repo_maintainers[week].setdefault(repo, set()).add(login)

    values: dict[str, float] = {}
    for week, repo_map in week_repo_maintainers.items():
        if repo_map:
            avg = sum(len(m) for m in repo_map.values()) / len(repo_map)
        else:
            avg = 0.0
        values[week] = avg

    return pd.Series(values, name="maintainer_count")


# ---------------------------------------------------------------------------
# Chart builder
# ---------------------------------------------------------------------------

def _make_chart(series: pd.Series, y_label: str) -> str:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=list(series.index), y=list(series.values), mode="lines+markers")
    )
    fig.update_layout(
        xaxis_title="Week",
        yaxis_title=y_label,
        margin={"t": 20, "b": 40},
        height=350,
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

_SECTION_TEMPLATE = """\
<section id="{id}">
  <h2>{title}</h2>
  <p><strong>Description:</strong> {description}</p>
  <p><strong>Objectives:</strong> {objectives}</p>
  <div class="chart">{chart_html}</div>
</section>
"""

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{org} — Community Activity Report</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body {{ font-family: sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ border-bottom: 2px solid #333; padding-bottom: 0.5rem; }}
    section {{ margin-bottom: 3rem; }}
    h2 {{ margin-bottom: 0.25rem; }}
    p {{ color: #444; margin: 0.25rem 0 0.75rem; }}
    .chart {{ margin-top: 1rem; }}
  </style>
</head>
<body>
  <h1>{org} — Community Activity Report</h1>
  <p>Period: {since} – {until}</p>
  {sections}
</body>
</html>
"""


def build_report(
    data_dir: Path,
    output_path: Path,
    since: datetime,
    until: datetime,
) -> None:
    org = data_dir.resolve().name

    issues, prs = load_org_items(data_dir)
    weeks = week_range(since, until)

    series_map = {
        "contributor-count": (
            metric_contributor_count(issues, prs, weeks),
            "Distinct Contributors",
        ),
        "updated-issues-count": (
            metric_updated_issues_count(issues, prs, weeks),
            "Issues + PRs Updated",
        ),
        "updated-since": (
            metric_updated_since(issues, prs, weeks),
            "Avg Days Since Last Update",
        ),
        "code-review-count": (
            metric_code_review_count(prs, weeks),
            "Avg Comments / PR",
        ),
        "issue-comment-frequency": (
            metric_issue_comment_frequency(issues, weeks),
            "Avg Comments / Issue",
        ),
        "pr-comment-frequency": (
            metric_pr_comment_frequency(prs, weeks),
            "Avg Comments / PR",
        ),
        "maintainer-count": (
            metric_maintainer_count(issues, prs, weeks),
            "Avg Maintainers / Repo",
        ),
    }

    sections_html = ""
    for meta in METRICS:
        series, y_label = series_map[meta["id"]]
        chart_html = _make_chart(series, y_label)
        sections_html += _SECTION_TEMPLATE.format(
            id=meta["id"],
            title=meta["title"],
            description=meta["description"],
            objectives=meta["objectives"],
            chart_html=chart_html,
        )

    html = _HTML_TEMPLATE.format(
        org=org,
        since=since.date(),
        until=until.date(),
        sections=sections_html,
    )
    output_path.write_text(html)
