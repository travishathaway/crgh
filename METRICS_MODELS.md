# Metrics models

The following file presents CHAOSS metrics models in a way that is friendlier for an LLM to read. These are also the specific metrics from these models that we'll actually be able to calculate based on the data we retrieve from GitHub.

The equations shown on this page use LaTeX syntax.


## Community Activity

### Contributor Count

Description: The number of active code commit authors, pr authors, review participants, issue authors, and issue comments participants over a certain period of time.

Objectives: Open source projects are comprised of a number of different contributors. Recognizing all contributors to a project is important in knowing who is helping with such activities as code development, event planning, and marketing efforts.

Implementation: $X=|\cup{A_i}|$.$A_i$=a contributor who is active over a certain period of time.

### Updated Issues Count

Description: The number of issues and pull requests updated over a certain period of time.

Objectives: Reveal how many people are actively discussing topics on a repository

Implementation: $X=A$, $A$=The number of issues updated over a certain period of time.

### Updated Since

Updated Since

Description: The average time per repository since the repository was last updated. This is the time between updates to issues and pull requests.

Objectives: This is a slight variation on the updated issue count except that here we focus on how often the repository is being updated.

Implementation: $X=\frac{\sum A_i }{B}$, $A_i$=The time of a repository since it was last updated, B=The number of repositories.

### Code Review Count

Description: The average number of review comments per pull request created over a certain period of time.

Objectives: To understand the nature of change request review practice within a repository, and across a collection of repositories. Change Request Reviews can help inform the quality of the software and the efficiency of development. Examining change request review processes and timeliness over time is helpful for characterizing the evolution of an open source software project. Exploration of Change Requests Reviews along with demographics of participants may highlight issues of DEI in a projects formal review process.

Implementation: $X=\frac{A}{B}$, $A$=The number of review comments over a certain period of time, B=The number of pull requests over a certain period of time.


### Issue Comment Frequency

Description: The average number of comments per issue created over a certain period of time.

Objectives: See how large discussions on issues are.

Implementation: $X=\frac{A}{B}$, $A$=The number of comments over a certain period of time, B=The number of issues over a certain period of time.

### Pull Request Comment Frequency

Description: The average number of comments per pull request created over a certain period of time.

Objectives: See how large discussions on pull requests are.

Implementation: $X=\frac{A}{B}$, $A$=The number of comments over a certain period of time, B=The number of pull requests over a certain period of time.

### Maintainer Count

Description: The average number of maintainers per repository over a certain period of time.

Objectives: To see how many active maintainers are participating for a given repository

Implementation: $X=\frac{A}{B}$, $A$=The number of maintainers, B=The number of repositories.

Special notes: This can only be done when we have access to data from multiple repositories at once.
