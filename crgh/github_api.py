"""GitHub REST API helpers for repo listing and counting."""

import requests


GITHUB_API = "https://api.github.com"


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def list_public_repos(org: str, token: str) -> list[str]:
    """Return names of all public, non-archived repos for an org."""
    repos = []
    url = f"{GITHUB_API}/orgs/{org}/repos"
    params = {"type": "public", "per_page": 100, "page": 1}

    while True:
        resp = requests.get(url, headers=_auth_headers(token), params=params)
        resp.raise_for_status()
        page = resp.json()
        if not page:
            break
        for repo in page:
            if not repo.get("archived", False):
                repos.append(repo["name"])
        if len(page) < 100:
            break
        params["page"] += 1

    return repos


_COUNT_QUERY = """
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    issues {
      totalCount
    }
    pullRequests {
      totalCount
    }
  }
}
"""


def count_issues_and_prs(org: str, repo: str, token: str) -> tuple[int, int]:
    """Return (issue_count, pr_count) for all states (open + closed) via GraphQL."""
    resp = requests.post(
        f"{GITHUB_API}/graphql",
        headers=_auth_headers(token),
        json={"query": _COUNT_QUERY, "variables": {"owner": org, "repo": repo}},
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    repo_data = data["data"]["repository"]
    return repo_data["issues"]["totalCount"], repo_data["pullRequests"]["totalCount"]
