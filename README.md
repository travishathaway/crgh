# CHAOSS Report for GitHub Organizations

This is a tool to generate reports based on CHAOSS metrics models for organizations in GitHub.


## Usage

Before using this tool, set a `GITHUB_TOKEN` as an environment variable. This is needed to query the public API with lower rate-limiting.

To first gather statistics for an organization, run the following command

```
crgh repo-stats <org-name> --token $GITHUB_TOKEN
```

This will return all public repositories that are not "public archives" and will list the number of pull requests and issues for each.

```json
{
  "repositories": [
    {
      "name": "repo-name",
      "issues": 123,
      "pull-requests": 200
    },
    {
      "name": "repo-name",
      "issues": 123,
      "pull-requests": 200
    }
  ]
}

You can save this as a file then feed it to the `gather-stats` command to grab all the information about issues and pull requests for a repository.

```
crgh gather-stats <repo-info-file> --output-dir <org-name> --since 2025-01-01 --token $GITHUB_TOKEN
```

This will save issue and pull request data from each repository and place it in whatever folder you would like.