import os
import requests
import time
from datetime import datetime
import pandas as pd


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

    def github_api_request(self, url, max_retries=3):
        """Handles API requests, including rate limits."""
        retries = 0

        while retries < max_retries:
            response = requests.get(url, headers=self.headers)

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

    def get_all_paginated_items(self, url):
        """Fetches all paginated results from GitHub API."""
        items = []
        page = 1
        while True:
            paginated_url = f"{url}?per_page=100&page={page}"
            response = self.github_api_request(paginated_url)

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
        df.to_csv(csv_path, mode="a", header=not file_exists, index=False)
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
                "default_branch": repo_data["default_branch"],
                "last_update": repo_data["updated_at"],
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
                        "fork_parent_id": repo_id,
                        "fork_parent_owner": repo_owner,
                        "fork_parent_name": repo_name,
                        "fork_id": fork["id"],
                        "fork_owner": fork["owner"]["login"],
                        "fork_name": fork["name"],
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

    def get_commit_data(
        self,
        fork_parent_id,
        fork_parent_owner,
        fork_parent_name,
        fork_id,
        fork_owner,
        fork_name,
        default_branch,
        commit_csv_path,
        resume_log_path,
        last_processed_page=None,
    ):
        """Get commit information and save to CSV."""
        page = last_processed_page if last_processed_page else 1
        while True:
            commits_url = (
                self.url + f"{fork_owner}/{fork_name}/commits?per_page=100&page={page}"
            )
            commits_response = self.github_api_request(commits_url)

            if commits_response.status_code == 404:
                print(
                    f"❌ Commits of fork {fork_owner}/{fork_name} not found. Skipping..."
                )
                break

            elif commits_response.status_code == 200:
                commits_data = commits_response.json()

                if not commits_data:  # If the page is empty, break the loop
                    with open(resume_log_path, "w") as f:
                        f.write(f"{fork_id},{page}")
                    break

                # Extract commit information
                commits = []
                for commit in commits_data:
                    commit_sha = commit["sha"]

                    # Check the detail of the commit
                    commit_url = (
                        self.url + f"{fork_owner}/{fork_name}/commits/{commit_sha}"
                    )
                    commit_response = self.github_api_request(commit_url)

                    if commit_response.status_code == 200:
                        commit_data = commit_response.json()

                    # Check if commit is in main repo
                    main_repo_commit_url = (
                        self.url
                        + f"{fork_parent_owner}/{fork_parent_name}/commits/{commit_sha}"
                    )
                    main_repo_commit_response = self.github_api_request(
                        main_repo_commit_url
                    )
                    is_in_main_repo = main_repo_commit_response.status_code == 200

                    # Check if commit is in main branch of main repo
                    compare_url = (
                        self.url
                        + f"{fork_parent_owner}/{fork_parent_name}/compare/{default_branch}...{commit_sha}"
                    )
                    compare_response = self.github_api_request(compare_url)
                    is_in_main_branch_main_repo = (
                        compare_response.status_code == 200
                        and "behind_by" in compare_response.json()
                    )

                    # Extract commit information
                    commit_info = {
                        "fork_parent_id": fork_parent_id,
                        "fork_id": fork_id,
                        "fork_owner": fork_owner,
                        "fork_name": fork_name,
                        "commit_sha": commit_sha,
                        "commit_size": commit_data["stats"]["total"],
                        "commit_create_at": commit["commit"]["author"]["date"],
                        "commit_pushed_at": commit["commit"]["committer"]["date"],
                        "is_in_main_repo": is_in_main_repo,
                        "is_in_main_branch_main_repo": is_in_main_branch_main_repo,
                    }

                    commits.append(commit_info)

                self.save_output(commits, commit_csv_path)
                print(
                    f"✅ Page {page} saved (Fork: {fork_id} of {fork_owner}/{fork_name})"
                )

                if len(commits) < 100:  # No more pages
                    with open(resume_log_path, "w") as f:
                        f.write(f"{fork_id},{page + 1}")
                    break

                page += 1
                with open(resume_log_path, "w") as f:
                    f.write(f"{fork_id},{page}")

                time.sleep(0.1)

        print(f"🚀 Finished processing fork {fork_id} of {fork_owner}/{fork_name}")

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
                    commits_data = self.get_all_paginated_items(commits_url)
                    commits = [commit["sha"] for commit in commits_data]

                    # Get all review comments in the PR
                    comments_url = (
                        self.url
                        + f"{repo_owner}/{repo_name}/pulls/{pr_number}/comments"
                    )
                    comments_data = self.get_all_paginated_items(comments_url)
                    comments = [comment["body"] for comment in comments_data]

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
                        "pr_body": pr["body"],
                        "pr_review_comments": comments,
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
        fork_parent_id,
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
            have_more_than_two_pr = len(pr_data) >= 2

        elif pr_response.status_code == 404:
            have_more_than_two_pr = False

        # Extract PR information
        pr_info = {
            "fork_parent_id": fork_parent_id,
            "fork_id": fork_id,
            "fork_owner": fork_owner,
            "fork_name": fork_name,
            "have_more_than_two_pr": have_more_than_two_pr,
        }

        self.save_output([pr_info], fork_pr_csv_path)

        # Save progress
        with open(resume_log_path, "w") as f:
            f.write(str(fork_id))

        print(
            f"🚀 Finished processing PRs of fork {fork_id} of {fork_owner}/{fork_name}"
        )
