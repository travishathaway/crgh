# JSON File Structure Reference

This document describes the structure of the JSON files produced by `crgh gather-stats`
and consumed by `crgh generate-report`. It was derived by inspecting files in the
`beeware/` directory (podium, briefcase, and toga repos, both issues and PRs).

---

## File Naming

| Pattern | Contents |
|---|---|
| `{repo}-issues.json` | All issues for that repo (no `pull_request` key in `data`) |
| `{repo}-pull-requests.json` | All pull requests for that repo (`pull_request` key present in `data`) |

Each file is a **JSON array** of perceval item objects.

---

## Top-Level Item Structure

Every item in both file types shares these root-level keys:

| Key | Type | Example / Notes |
|---|---|---|
| `backend_name` | string | `"GitHub"` |
| `backend_version` | string | `"1.0.0"` |
| `perceval_version` | string | `"1.4.6"` |
| `timestamp` | float | Unix timestamp — when perceval collected this item |
| `origin` | string | `"https://github.com/beeware/podium"` |
| `uuid` | string | SHA-1 hash uniquely identifying this item |
| `updated_on` | float | Unix timestamp — when the item was last updated on GitHub |
| `classified_fields_filtered` | null | Always null |
| `category` | string | Always `"issue"` (used for both issues and PRs by perceval) |
| `search_fields` | object | `{"item_id": 123, "owner": "beeware", "repo": "podium"}` |
| `tag` | string | Same as `origin` |
| `data` | object | Full GitHub API payload — see below |

### `search_fields`

| Key | Type | Notes |
|---|---|---|
| `item_id` | integer | GitHub issue/PR number |
| `owner` | string | GitHub org or user name |
| `repo` | string | Repository name |

---

## `data` Key — Shared Fields (Issues and PRs)

| Key | Type | Example / Notes |
|---|---|---|
| `url` | string | GitHub API URL for this issue/PR |
| `repository_url` | string | GitHub API URL for the repo |
| `labels_url` | string | URL template |
| `comments_url` | string | API URL for comments |
| `events_url` | string | API URL for events |
| `html_url` | string | Web URL, e.g. `https://github.com/beeware/podium/issues/48` |
| `id` | integer | GitHub internal numeric ID |
| `node_id` | string | GraphQL node ID |
| `number` | integer | Issue/PR number in the repo |
| `title` | string | Title text |
| `user` | object | Author — see [User Object](#user-object) |
| `labels` | array | Array of [Label Objects](#label-object) |
| `state` | string | `"open"` or `"closed"` |
| `locked` | boolean | |
| `assignees` | array | Array of User Objects |
| `milestone` | object\|null | Milestone object or null |
| `comments` | integer | Total number of comments **at time of collection** |
| `created_at` | string | ISO 8601, e.g. `"2020-02-13T23:05:35Z"` |
| `updated_at` | string | ISO 8601 |
| `closed_at` | string\|null | ISO 8601 or null |
| `assignee` | object\|null | Primary assignee User Object or null |
| `author_association` | string | See [Author Association Values](#author-association-values) |
| `type` | null | Always null |
| `active_lock_reason` | null | null unless locked |
| `sub_issues_summary` | object | `{"total": 0, "completed": 0, "percent_completed": 0}` |
| `issue_dependencies_summary` | object | `{"blocked_by": [], "total_blocked_by": 0, "blocking": [], "total_blocking": 0}` |
| `body` | string | Markdown body text |
| `closed_by` | object\|null | User Object who closed it, or null |
| `reactions` | object | See [Reactions Object](#reactions-object) |
| `timeline_url` | string | API URL for the timeline |
| `performed_via_github_app` | null | Always null |
| `state_reason` | string\|null | e.g. `"completed"` for closed issues, null otherwise |
| `pinned_comment` | null | Always null |
| `user_data` | object | Extended user profile — see [User Data Object](#user-data-object) |
| `assignee_data` | object | Empty object or assignee details |
| `assignees_data` | array | Array of User Data Objects |
| `comments_data` | array | Array of [Comment Objects](#comment-object) |

---

## `data` Key — PR-Only Fields

These keys appear **only** in `*-pull-requests.json` files:

| Key | Type | Notes |
|---|---|---|
| `draft` | boolean | Whether the PR is a draft |
| `pull_request` | object | See below |

### `data.pull_request`

| Key | Type | Example |
|---|---|---|
| `url` | string | GitHub API URL for the PR |
| `html_url` | string | Web URL for the PR |
| `diff_url` | string | URL to the `.diff` |
| `patch_url` | string | URL to the `.patch` |
| `merged_at` | string\|null | ISO 8601 merge timestamp, or null if not merged |

> **How to tell issues from PRs:** Check for `"pull_request" in item["data"]`. This key is absent on issues and present on PRs.

---

## User Object

Appears in `data.user`, `data.assignee`, `data.assignees[]`, `data.closed_by`, and inside comments.

| Key | Type | Notes |
|---|---|---|
| `login` | string | GitHub username |
| `id` | integer | GitHub user ID |
| `node_id` | string | GraphQL node ID |
| `avatar_url` | string | |
| `gravatar_id` | string | Empty string |
| `url` | string | API URL |
| `html_url` | string | GitHub profile URL |
| `type` | string | `"User"` or `"Bot"` |
| `user_view_type` | string | `"public"` |
| `site_admin` | boolean | |
| *(various `_url` fields)* | string | API URL templates |

---

## User Data Object

Appears in `data.user_data` and inside comments as `user_data`. Extends the User Object with:

| Key | Type | Notes |
|---|---|---|
| `name` | string\|null | Full name |
| `company` | string\|null | Company affiliation |
| `blog` | string | Website (may be empty string) |
| `location` | string\|null | |
| `email` | string\|null | Public email |
| `hireable` | boolean\|null | |
| `bio` | string\|null | Profile bio |
| `twitter_username` | string\|null | |
| `public_repos` | integer | |
| `public_gists` | integer | |
| `followers` | integer | |
| `following` | integer | |
| `created_at` | string | ISO 8601 — GitHub account creation date |
| `updated_at` | string | ISO 8601 |
| `organizations` | array | Array of org objects the user belongs to |

---

## Comment Object

Each element in `data.comments_data[]`:

| Key | Type | Notes |
|---|---|---|
| `url` | string | API URL for the comment |
| `html_url` | string | Web URL for the comment |
| `issue_url` | string | API URL for the parent issue/PR |
| `id` | integer | Comment ID |
| `node_id` | string | GraphQL node ID |
| `user` | object | User Object of the commenter |
| `created_at` | string | ISO 8601 |
| `updated_at` | string | ISO 8601 (last edit time) |
| `body` | string | Markdown comment text |
| `author_association` | string | Commenter's association to the repo |
| `pin` | null | Always null |
| `reactions` | object | Reactions Object |
| `performed_via_github_app` | null | Always null |
| `user_data` | object | User Data Object for the commenter |
| `reactions_data` | array | Array of individual reaction objects |

### `reactions_data` item

| Key | Type | Notes |
|---|---|---|
| `id` | integer | Reaction ID |
| `node_id` | string | |
| `user` | object | User Object who reacted |
| `content` | string | `"+1"`, `"heart"`, `"rocket"`, etc. |
| `created_at` | string | ISO 8601 |
| `user_data` | object | User Data Object |

---

## Reactions Object

Appears in `data.reactions` and in `comments_data[].reactions`:

| Key | Type |
|---|---|
| `url` | string |
| `total_count` | integer |
| `+1` | integer |
| `-1` | integer |
| `laugh` | integer |
| `hooray` | integer |
| `confused` | integer |
| `heart` | integer |
| `rocket` | integer |
| `eyes` | integer |

---

## Label Object

Each element in `data.labels[]`:

| Key | Type | Notes |
|---|---|---|
| `id` | integer | |
| `node_id` | string | |
| `url` | string | API URL |
| `name` | string | e.g. `"bug"`, `"enhancement"`, `"good first issue"` |
| `color` | string | Hex color without `#`, e.g. `"d73a4a"` |
| `default` | boolean | Whether it's a default GitHub label |
| `description` | string | |

---

## Author Association Values

Used in `data.author_association` and in `comments_data[].author_association`:

| Value | Meaning |
|---|---|
| `"OWNER"` | Repository owner |
| `"MEMBER"` | Member of the owning organization |
| `"COLLABORATOR"` | Invited collaborator on the repo |
| `"CONTRIBUTOR"` | Has at least one merged commit |
| `"NONE"` | No special relationship |

> **Used by `generate-report`:** `OWNER`, `MEMBER`, and `COLLABORATOR` are treated as maintainers for the Maintainer Count metric.

---

## How Metrics Map to Fields

| Metric | Field(s) used | Grouping field |
|---|---|---|
| Contributor Count | `data.user.login`, `data.comments_data[].user.login` | `data.created_at` |
| Updated Issues Count | `data.updated_at` (any item updated in that week) | `data.updated_at` |
| Updated Since | `data.updated_at`, `search_fields.owner/repo` | week end snapshot |
| Code Review Count | `data.comments` (PRs only) | `data.created_at` |
| Issue Comment Frequency | `data.comments` (issues only) | `data.created_at` |
| PR Comment Frequency | `data.comments` (PRs only) | `data.created_at` |
| Maintainer Count | `data.author_association` ∈ {OWNER,MEMBER,COLLABORATOR}, `data.user.login` | `data.created_at` |

> **Note on `data.comments`:** This is a snapshot integer captured at collection time — it counts all comments on the item as of when `gather-stats` was run. The `comments_data` array contains the actual comment objects and may be used for more granular analysis.
