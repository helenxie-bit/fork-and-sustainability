import os
import requests
import time
from datetime import datetime
import pandas as pd
import csv


class API:
    def __init__(self, args, token):
        self.args = args
        self.token = os.getenv("GITHUB_TOKEN")
        self.url = "https://api.github.com/repos/"
        self.headers = {"Authorization": f"token {self.token}"} if self.token else {}

    def pull_repo(self, owner, repo):
        repo_url = self.url + owner + "/" + repo
        repo_response = requests.get(repo_url, headers=self.headers)

        try:
            repo_response.raise_for_status()
            print(f"Successfully fetched '{owner}/{repo}'")
            repo_json = repo_response.json()
            repo_id = repo_json["id"]
            repo_owner = repo_json["owner"]["login"]
            return repo_response
        except Exception as e:
            print(
                f"Error: Unable to fetch '{owner}/{repo}'. Status code: {repo_response.status_code}"
            )
            print(f"Response: {repo_response.text}")
            return

    def github_api_request(self, url, max_retries=3, headers=None):
        """Handles API requests, including rate limits."""
        retries = 0

        while retries < max_retries:
            response = requests.get(
                url, headers=self.headers if not headers else headers
            )

            if response.status_code == 200 or response.status_code == 404:
                return response

            elif response.status_code == 403:  # Rate limit hit
                reset_time = int(response.headers["X-RateLimit-Reset"])
                reset_time_str = datetime.fromtimestamp(reset_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )  # Convert Unix timestamps to human-readable format
                current_time = time.time()
                current_time_str = datetime.fromtimestamp(current_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )  # Convert Unix timestamps to human-readable format
                wait_time = reset_time - current_time
                print(
                    f"🚨 Rate limit exceeded! Waiting {int(wait_time)} seconds before retrying...(Current time: {current_time_str}, Reset time: {reset_time_str})"
                )
                time.sleep(wait_time + 1)

            else:
                print(f"❌ API error ({response.status_code}): {response.text}")
                retries += 1
                if retries < max_retries:
                    print(f"🔄 Retrying ({retries}/{max_retries}) in 5 seconds...")
                    time.sleep(5)  # Short delay before retrying
                else:
                    print(
                        f"❌ API request failed after {max_retries} attempts. Exiting."
                    )
                    exit(1)  # Exit with error

        return None

    def get_all_paginated_items(self, url, headers=None):
        """Fetches all paginated results from GitHub API."""
        items = []
        page = 1
        while True:
            paginated_url = f"{url}?per_page=100&page={page}"
            response = self.github_api_request(url=paginated_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                items.extend(data)
                if len(data) < 100:  # No more pages
                    break
                page += 1
            else:
                print(f"❌ Error fetching paginated items: {response.status_code}")
                break
        return items

    def save_output(self, data, csv_path):
        """Saves data to CSV, appending if file exists."""
        # Check if the output file already exists
        file_exists = os.path.exists(csv_path)

        # Convert data to DataFrame and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(
            csv_path,
            mode="a",
            header=not file_exists,
            index=False,
            quoting=csv.QUOTE_ALL,
        )
        return True

    def get_repo_data(self, repo_owner, repo_name, repo_csv_path, missing_csv_path):
        """Get repository general information and save to CSV."""
        # Get general repository information
        repo_url = self.url + f"{repo_owner}/{repo_name}"
        repo_response = self.github_api_request(repo_url)

        # Check for API errors
        if repo_response.status_code == 404:
            # Save missing repo information
            self.save_output([{"repo_name": repo_name}], missing_csv_path)
            print(f"❌ Repository {repo_owner}/{repo_name} not found. Skipping...")

        elif repo_response.status_code == 200:
            # Parse response JSON and extract repository information
            repo_data = repo_response.json()
            repo_info = {
                "repo_id": repo_data["id"],
                "repo_owner": repo_data["owner"]["login"],
                "repo_name": repo_data["name"],
                "created_at": repo_data["created_at"],
                "project_size": repo_data["size"],
                "num_forks": repo_data["forks_count"],
                "num_stars": repo_data["stargazers_count"],
                "default_branch": repo_data["default_branch"],
                "last_update": repo_data["updated_at"],
                "is_archived": repo_data["archived"],
                "repo_url": repo_data["html_url"],
            }

            # Save repo information
            self.save_output([repo_info], repo_csv_path)
            print(
                f"✅ Repository {repo_owner}/{repo_name} information saved to {repo_csv_path}"
            )

    def get_fork_data(self, repo_id, repo_owner, repo_name, fork_csv_path):
        """Get fork information and save to CSV."""
        page = 1
        while True:
            fork_url = (
                self.url + f"{repo_owner}/{repo_name}/forks?per_page=100&page={page}"
            )
            fork_response = self.github_api_request(fork_url)

            if fork_response.status_code == 404:
                print(
                    f"❌ Forks of repository {repo_owner}/{repo_name} not found. Skipping..."
                )
                break

            elif fork_response.status_code == 200:
                forks_data = fork_response.json()

                if not forks_data:  # If the page is empty, break the loop
                    break

                # Extract fork information
                for fork in forks_data:
                    fork_info = {
                        "repo_id": repo_id,
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "fork_id": fork["id"],
                        "fork_owner": fork["owner"]["login"],
                        "fork_owner_id": fork["owner"]["id"],
                        "fork_name": fork["name"],
                        "fork_default_branch": fork["default_branch"],
                        "fork_created_at": fork["created_at"],
                        "fork_url": fork["html_url"],
                    }

                    self.save_output([fork_info], fork_csv_path)

                    print(
                        f"✅ Fork {fork['owner']['login']}/{fork['name']} of Repository {repo_owner}/{repo_name} information saved to {fork_csv_path}"
                    )

                if len(forks_data) < 100:  # No more pages
                    break

            page += 1
            time.sleep(0.1)  # Avoid hitting concurrent request limit

    def get_repo_commit_data(
        self,
        repo_id,
        repo_owner,
        repo_name,
        repo_commit_csv_path,
        resume_log_path,
        last_processed_page=None,
    ):
        """Get commit information of repository and save to CSV."""
        page = last_processed_page if last_processed_page else 1
        while True:
            commits_url = (
                self.url + f"{repo_owner}/{repo_name}/commits?per_page=100&page={page}"
            )
            commits_response = self.github_api_request(commits_url)

            if commits_response.status_code == 404:
                print(
                    f"❌ Commits of repository {repo_owner}/{repo_name} not found. Skipping..."
                )
                break

            elif commits_response.status_code == 200:
                commits_data = commits_response.json()

                if not commits_data:  # If the page is empty, break the loop
                    with open(resume_log_path, "w") as f:
                        f.write(f"{repo_id},{page}")
                    break

                # Extract fork information
                commits = []
                for commit in commits_data:
                    commit_sha = commit["sha"]

                    # Check the detail of the commit
                    commit_url = (
                        self.url + f"{repo_owner}/{repo_name}/commits/{commit_sha}"
                    )
                    commit_response = self.github_api_request(commit_url)

                    if commit_response.status_code == 200:
                        commit_data = commit_response.json()

                    commit_info = {
                        "repo_id": repo_id,
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "commit_sha": commit_sha,
                        "commit_author": (commit.get("author") or {}).get(
                            "login", "unknown"
                        ),
                        "commit_author_id": (commit.get("author") or {}).get(
                            "id", "unknown"
                        ),
                        "commit_size": commit_data.get("stats", {}).get(
                            "total", 0
                        ),  # (TODO): Should we keep it or delete it to save requests?
                        "commit_created_at": commit["commit"]["author"]["date"],
                        "commit_pushed_at": commit["commit"]["committer"]["date"],
                    }
                    commits.append(commit_info)

                self.save_output(commits, repo_commit_csv_path)

                print(
                    f"✅ Page {page} of {repo_owner}/{repo_name} saved to {repo_commit_csv_path}"
                )

                if len(commits) < 100:  # No more pages
                    with open(resume_log_path, "w") as f:
                        f.write(f"{repo_id},{page + 1}")
                    break

            page += 1
            with open(resume_log_path, "w") as f:
                f.write(f"{repo_id},{page}")

            time.sleep(0.1)  # Avoid hitting concurrent request limit

        print(f"🚀 Finished processing commits of {repo_owner}/{repo_name}")

    def get_fork_commit_data(
        self,
        repo_id,
        repo_owner,
        repo_name,
        repo_default_branch,
        fork_id,
        fork_owner,
        fork_name,
        fork_default_branch,
        fork_commit_csv_path,
        resume_log_path,
    ):
        """Get fork commit information that is NOT in the main repository and save to CSV."""
        compare_url = (
            self.url
            + f"{repo_owner}/{repo_name}/compare/{repo_default_branch}...{fork_owner}:{fork_default_branch}"
        )
        compare_response = self.github_api_request(compare_url)

        if compare_response.status_code == 200:
            compare_data = compare_response.json()
            fork_commits = compare_data.get(
                "commits", []
            )  # Only new commits in the fork
        else:
            print(
                f"❌ Error fetching compare data for {fork_owner}/{fork_name} (Error Code: {compare_response.status_code}). Skipping..."
            )
            return

        if not fork_commits:
            print(
                f"❗ No unique commits found in fork {fork_owner}/{fork_name}. Skipping..."
            )
            return

        # Process fork commits
        for commit in fork_commits:
            commit_sha = commit["sha"]
            # Check the detail of the commit
            # commit_url = (
            #     self.url + f"{fork_owner}/{fork_name}/commits/{commit_sha}"
            # )
            # commit_response = self.github_api_request(commit_url)

            # if commit_response.status_code == 200:
            #     commit_data = commit_response.json()

            commit_info = {
                "repo_id": repo_id,
                "fork_id": fork_id,
                "fork_owner": fork_owner,
                "fork_name": fork_name,
                "commit_sha": commit_sha,
                "commit_author": (commit.get("author") or {}).get("login", "unknown"),
                "commit_author_id": (commit.get("author") or {}).get("id", "unknown"),
                # "commit_size": commit_data.get("stats", {}).get("total", 0), # (TODO): Commented out to save requests. Should we add it back?
                "commit_created_at": commit["commit"]["author"]["date"],
                "commit_pushed_at": commit["commit"]["committer"]["date"],
            }
            self.save_output([commit_info], fork_commit_csv_path)
            print(
                f"✅ Commit {commit_sha} of fork {fork_owner}/{fork_name} saved to {fork_commit_csv_path}"
            )

        # Save progress
        with open(resume_log_path, "w") as f:
            f.write(str(fork_id))

        print(f"🚀 Finished processing commits of {fork_owner}/{fork_name}")

    def get_repo_pr_data(
        self,
        repo_id,
        repo_owner,
        repo_name,
        repo_pr_csv_path,
        resume_log_path,
        last_processed_page=None,
    ):
        """Get PR information of repository and save to CSV."""
        page = last_processed_page if last_processed_page else 1
        while True:
            pr_url = (
                self.url
                + f"{repo_owner}/{repo_name}/pulls?state=all&per_page=100&page={page}"
            )
            pr_response = self.github_api_request(pr_url)

            if pr_response.status_code == 404:
                print(
                    f"❌ PRs of repository {repo_owner}/{repo_name} not found. Skipping..."
                )
                break

            elif pr_response.status_code == 200:
                pr_data = pr_response.json()

                if not pr_data:  # If the page is empty, break the loop
                    with open(resume_log_path, "w") as f:
                        f.write(f"{repo_id},{page}")
                    break

                prs = []
                for pr in pr_data:
                    pr_number = pr["number"]

                    # Get all commits in the PR
                    commits_url = (
                        self.url + f"{repo_owner}/{repo_name}/pulls/{pr_number}/commits"
                    )
                    commits_data = self.get_all_paginated_items(commits_url, None)
                    commits = [commit["sha"] for commit in commits_data]

                    # Get all review comments in the PR
                    comments_url = (
                        self.url
                        + f"{repo_owner}/{repo_name}/pulls/{pr_number}/comments"
                    )
                    comments_data = self.get_all_paginated_items(comments_url, None)
                    comments = [comment["body"] for comment in comments_data]

                    # Replace newline characters within each comment
                    cleaned_comments = [
                        comment.replace("\n", " ") for comment in comments
                    ]
                    # Join the list into a single string with '||' as a delimiter
                    cleaned_comments_str = "||".join(cleaned_comments)

                    # Extract PR information
                    pr_info = {
                        "repo_id": repo_id,
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "pr_id": pr["id"],
                        "pr_number": pr_number,
                        "pr_associated_commits": commits,
                        "pr_created_at": pr["created_at"],
                        "pr_state": pr["state"],
                        "pr_merged_at": pr["merged_at"],
                        "pr_closed_at": pr["closed_at"],
                        "pr_review_comments": cleaned_comments_str,
                    }

                    prs.append(pr_info)

                self.save_output(prs, repo_pr_csv_path)
                print(
                    f"✅ Page {page} of {repo_owner}/{repo_name} saved to {repo_pr_csv_path}"
                )

                if len(prs) < 100:  # No more pages
                    with open(resume_log_path, "w") as f:
                        f.write(f"{repo_id},{page + 1}")
                    break

                page += 1
                with open(resume_log_path, "w") as f:
                    f.write(f"{repo_id},{page}")

                time.sleep(0.1)

        print(f"🚀 Finished processing PRs of {repo_owner}/{repo_name}")

    def get_fork_pr_data(
        self,
        repo_id,
        fork_id,
        fork_owner,
        fork_name,
        fork_pr_csv_path,
        resume_log_path,
    ):
        """Get PR information of fork and save to CSV."""
        pr_url = self.url + f"{fork_owner}/{fork_name}/pulls?state=all"
        pr_response = self.github_api_request(pr_url)

        if pr_response.status_code == 200:
            pr_data = pr_response.json()
            has_more_than_two_pr = len(pr_data) >= 2

        elif pr_response.status_code == 404:
            has_more_than_two_pr = False

        # Extract PR information
        pr_info = {
            "repo_id": repo_id,
            "fork_id": fork_id,
            "fork_owner": fork_owner,
            "fork_name": fork_name,
            "has_more_than_two_pr": has_more_than_two_pr,
        }

        self.save_output([pr_info], fork_pr_csv_path)

        # Save progress
        with open(resume_log_path, "w") as f:
            f.write(str(fork_id))

        print(
            f"🚀 Finished processing PRs of fork {fork_id} of {fork_owner}/{fork_name}"
        )

    def get_star_data(
        self,
        repo_id,
        repo_owner,
        repo_name,
        star_csv_path,
        resume_log_path,
        last_processed_page,
    ):
        """Get stars information of repository and save to CSV."""
        page = last_processed_page if last_processed_page else 1
        while True:
            stargazers_url = (
                self.url
                + f"{repo_owner}/{repo_name}/stargazers?per_page=100&page={page}"
            )
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.star+json",
            }
            stargazers_response = self.github_api_request(
                url=stargazers_url, headers=headers
            )

            if stargazers_response.status_code == 200:
                stargazers_data = stargazers_response.json()

                if not stargazers_data:  # If the page is empty, break the loop
                    with open(resume_log_path, "w") as f:
                        f.write(f"{repo_id},{page}")
                    break

                # Extract release information
                stars = []
                for star in stargazers_data:
                    star_info = {
                        "repo_id": repo_id,
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "star_id": star["user"]["id"],
                        "star_login": star["user"]["login"],
                        "starred_at": star["starred_at"],
                    }
                    stars.append(star_info)

                self.save_output(stars, star_csv_path)

                print(
                    f"✅ Page {page} of Repository {repo_owner}/{repo_name} information saved to {star_csv_path}"
                )

                if len(stargazers_data) < 100:  # No more pages
                    with open(resume_log_path, "w") as f:
                        f.write(f"{repo_id},{page + 1}")
                    break

            page += 1
            with open(resume_log_path, "w") as f:
                f.write(f"{repo_id},{page}")

            time.sleep(0.1)  # Avoid hitting concurrent request limit

        print(f"🚀 Finished processing Stars of Repository {repo_owner}/{repo_name}")

    def get_release_data(
        self,
        repo_id,
        repo_owner,
        repo_name,
        release_csv_path,
        resume_log_path,
        last_processed_page,
    ):
        """Get release information of repository and save to CSV."""
        page = last_processed_page if last_processed_page else 1
        while True:
            releases_url = (
                self.url + f"{repo_owner}/{repo_name}/releases?per_page=100&page={page}"
            )
            releases_response = self.github_api_request(releases_url)

            if releases_response.status_code == 404:
                print(
                    f"❌ Release of repository {repo_owner}/{repo_name} not found. Skipping..."
                )
                break

            elif releases_response.status_code == 200:
                releases_data = releases_response.json()

                if not releases_data:  # If the page is empty, break the loop
                    with open(resume_log_path, "w") as f:
                        f.write(f"{repo_id},{page}")
                    break

                # Extract release information
                releases = []
                for release in releases_data:
                    release_info = {
                        "repo_id": repo_id,
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "release_id": release["id"],
                        "release_tag": release["tag_name"],
                        "release_created_at": release["created_at"],
                        "release_published_at": release["published_at"],
                        "release_url": release["html_url"],
                    }
                    releases.append(release_info)

                self.save_output(releases, release_csv_path)

                print(
                    f"✅ Page {page} of Repository {repo_owner}/{repo_name} information saved to {release_csv_path}"
                )

                if len(releases_data) < 100:  # No more pages
                    with open(resume_log_path, "w") as f:
                        f.write(f"{repo_id},{page + 1}")
                    break

            page += 1
            with open(resume_log_path, "w") as f:
                f.write(f"{repo_id},{page}")

            time.sleep(0.1)  # Avoid hitting concurrent request limit

        print(f"🚀 Finished processing Releases of Repository {repo_owner}/{repo_name}")
