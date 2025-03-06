import argparse
from dotenv import load_dotenv
import os
from API.api import API
import pandas as pd
from pprint import pprint
import constants
import numpy as np
import ast
from datetime import datetime, timedelta


def check_file_exists(filepath, msg):
    """Helper function to check if a file exists."""
    if not os.path.exists(filepath):
        print(f"Error: {msg}")
        exit(1)


def API_check(args):
    """Handles basic API checks."""
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: No GitHub token provided.")
        exit(1)
    github_api = API(args, token)

    check_file_exists(
        constants.PROJECTS_LIST, f"{constants.PROJECTS_LIST} does not exist."
    )
    df_projects = pd.read_csv(constants.PROJECTS_LIST)

    for project in [df_projects["listname"][0]]:
        owner = "apache"
        repo = project.strip()
        response = github_api.pull_repo(owner, repo)
        pprint(response.json())


def resume_from_checkpoint(resume_log_path, with_page=False):
    """Resumes from the last processed checkpoint."""
    if os.path.exists(resume_log_path):
        with open(resume_log_path, "r") as f:
            data = f.read().strip().split(",")

        if with_page and len(data) == 2:  # Handle case with page number
            last_processed_repo, last_processed_page = data
            return last_processed_repo, (
                int(last_processed_page) if last_processed_page.isdigit() else 1
            )
        else:
            return data[0]  # Handle case without page number

    return (None, 1) if with_page else None


def handle_repo_data(github_api, name):
    """Handles repo general information collection."""
    check_file_exists(
        constants.PROJECTS_LIST, f"{constants.PROJECTS_LIST} does not exist."
    )
    df_projects = pd.read_csv(constants.PROJECTS_LIST)

    for project in df_projects["pj_alias"]:
        repo_owner = "apache"
        repo_name = project.strip()  # Remove leading/trailing whitespace
        github_api.get_repo_data(
            repo_owner, repo_name, constants.REPO_CSV_PATH, constants.MISSING_CSV_PATH
        )


def handle_fork_data(github_api, name):
    """Handles fork data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)
    filter_repos = df_repos[df_repos["teammate"] == name]

    for repo_id, repo_owner, repo_name in zip(
        filter_repos["repo_id"], filter_repos["repo_owner"], filter_repos["repo_name"]
    ):
        github_api.get_fork_data(
            repo_id, repo_owner, repo_name, constants.FORK_CSV_PATH
        )


def handle_repo_commit_data(github_api, name):
    """Handles commit data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)
    filter_repos = df_repos[df_repos["teammate"] == name]

    # Resume from last processed fork
    resume_log_path = constants.RESUME_LOG_PATH_REPO_COMMIT
    last_processed_repo, last_processed_page = resume_from_checkpoint(
        resume_log_path, with_page=True
    )

    for repo_id, repo_owner, repo_name in zip(
        filter_repos["repo_id"], filter_repos["repo_owner"], filter_repos["repo_name"]
    ):
        # Resume processing if interrupted
        if last_processed_repo and str(repo_id) != last_processed_repo:
            continue  # Skip to the last processed fork

        github_api.get_repo_commit_data(
            repo_id,
            repo_owner,
            repo_name,
            constants.REPO_COMMIT_CSV_PATH,
            resume_log_path,
            last_processed_page,
        )

        last_processed_repo = None  # Reset last processed repo
        last_processed_page = None  # Reset last processed page


def handle_fork_commit_data(github_api, name):
    """Handles commit data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)

    check_file_exists(
        constants.FORK_CSV_PATH,
        f"{constants.FORK_CSV_PATH} does not exist. Please run choice 2 first.",
    )
    df_forks = pd.read_csv(constants.FORK_CSV_PATH)
    filter_forks = df_forks[df_forks["teammate"] == name]

    # Resume from last processed fork
    resume_log_path = constants.RESUME_LOG_PATH_FORK_COMMIT
    last_processed_fork = resume_from_checkpoint(resume_log_path, with_page=False)

    for fork_id, fork_owner, fork_name in zip(
        filter_forks["fork_id"], filter_forks["fork_owner"], filter_forks["fork_name"]
    ):
        # Resume processing if interrupted
        if last_processed_fork and str(fork_id) != last_processed_fork:
            continue  # Skip to the last processed fork
        if last_processed_fork and str(fork_id) == last_processed_fork:
            last_processed_fork = None
            continue

        repo_id = df_forks[df_forks["fork_id"] == fork_id]["repo_id"].values[0]
        repo_owner = df_forks[df_forks["fork_id"] == fork_id]["repo_owner"].values[0]
        repo_name = df_forks[df_forks["fork_id"] == fork_id]["repo_name"].values[0]
        repo_default_branch = df_repos[df_repos["repo_id"] == repo_id][
            "default_branch"
        ].values[0]
        fork_default_branch = df_forks[df_forks["fork_id"] == fork_id][
            "fork_default_branch"
        ].values[0]

        github_api.get_fork_commit_data(
            repo_id,
            repo_owner,
            repo_name,
            repo_default_branch,
            fork_id,
            fork_owner,
            fork_name,
            fork_default_branch,
            constants.FORK_COMMIT_CSV_PATH,
            resume_log_path,
        )


def handle_repo_pr_data(github_api, name):
    """Handles repo PR data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)
    filter_repos = df_repos[df_repos["teammate"] == name]

    # Resume from last processed fork
    resume_log_path = constants.RESUME_LOG_PATH_REPO_PR
    last_processed_repo, last_processed_page = resume_from_checkpoint(
        resume_log_path, with_page=True
    )

    for repo_id, repo_owner, repo_name in zip(
        filter_repos["repo_id"], filter_repos["repo_owner"], filter_repos["repo_name"]
    ):
        # Resume processing if interrupted
        if last_processed_repo and str(repo_id) != last_processed_repo:
            continue  # Skip to the last processed repo

        github_api.get_repo_pr_data(
            repo_id,
            repo_owner,
            repo_name,
            constants.REPO_PR_CSV_PATH,
            resume_log_path,
            last_processed_page,
        )

        last_processed_repo = None  # Reset last processed repo
        last_processed_page = None  # Reset last processed page


def handle_fork_pr_data(github_api, name):
    """Handles fork PR data collection."""
    check_file_exists(
        constants.FORK_CSV_PATH,
        f"{constants.FORK_CSV_PATH} does not exist. Please run choice 2 first.",
    )
    df_forks = pd.read_csv(constants.FORK_CSV_PATH)
    filter_forks = df_forks[df_forks["teammate"] == name]

    # Resume from last processed fork
    resume_log_path = constants.RESUME_LOG_PATH_FORK_PR
    last_processed_fork = resume_from_checkpoint(resume_log_path, with_page=False)

    for fork_parent_id, fork_id, fork_owner, fork_name in zip(
        filter_forks["repo_id"],
        filter_forks["fork_id"],
        filter_forks["fork_owner"],
        filter_forks["fork_name"],
    ):
        # Resume processing if interrupted
        if last_processed_fork and str(fork_id) != last_processed_fork:
            continue  # Skip to the last processed fork
        if last_processed_fork and str(fork_id) == last_processed_fork:
            last_processed_fork = None  # Reset last processed fork
            continue

        github_api.get_fork_pr_data(
            fork_parent_id,
            fork_id,
            fork_owner,
            fork_name,
            constants.FORK_PR_CSV_PATH,
            constants.RESUME_LOG_PATH_FORK_PR,
        )


def handle_star_data(github_api, name):
    """Handles fork data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)
    filter_repos = df_repos[df_repos["teammate"] == name]

    # Resume from last processed fork
    resume_log_path = constants.RESUME_LOG_PATH_STAR
    last_processed_repo, last_processed_page = resume_from_checkpoint(
        resume_log_path, with_page=True
    )

    for repo_id, repo_owner, repo_name in zip(
        filter_repos["repo_id"], filter_repos["repo_owner"], filter_repos["repo_name"]
    ):
        # Resume processing if interrupted
        if last_processed_repo and str(repo_id) != last_processed_repo:
            continue  # Skip to the last processed repo

        github_api.get_star_data(
            repo_id,
            repo_owner,
            repo_name,
            constants.STAR_CSV_PATH,
            resume_log_path,
            last_processed_page,
        )

        last_processed_repo = None  # Reset last processed repo
        last_processed_page = None  # Reset last processed page


def handle_release_data(github_api, name):
    """Handles fork data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)
    filter_repos = df_repos[df_repos["teammate"] == name]

    # Resume from last processed fork
    resume_log_path = constants.RESUME_LOG_PATH_RELEASE
    last_processed_repo, last_processed_page = resume_from_checkpoint(
        resume_log_path, with_page=True
    )

    for repo_id, repo_owner, repo_name in zip(
        filter_repos["repo_id"], filter_repos["repo_owner"], filter_repos["repo_name"]
    ):
        # Resume processing if interrupted
        if last_processed_repo and str(repo_id) != last_processed_repo:
            continue  # Skip to the last processed repo

        github_api.get_release_data(
            repo_id,
            repo_owner,
            repo_name,
            constants.RELEASE_CSV_PATH,
            resume_log_path,
            last_processed_page,
        )

        last_processed_repo = None  # Reset last processed repo
        last_processed_page = None  # Reset last processed page


def preprocess_sustainability_data(teammate):
    # Load datasets
    repo_info = pd.read_csv(constants.REPO_CSV_PATH)
    project_list = pd.read_csv(constants.PROJECTS_LIST)
    star_info = pd.read_csv(constants.STAR_CSV_PATH)
    release_info = pd.read_csv(constants.RELEASE_CSV_PATH)

    # Merge 'status' from project_list into repo_info
    if teammate is not None:
        repo_info = repo_info[repo_info["teammate"] == teammate]
    repo_info = repo_info.merge(
        project_list[["pj_alias", "status"]],
        left_on="repo_name",
        right_on="pj_alias",
        how="left",
    )

    # Convert 'starred_at' and 'release_published_at' to datetime
    star_info["starred_at"] = pd.to_datetime(star_info["starred_at"])
    release_info["release_published_at"] = pd.to_datetime(
        release_info["release_published_at"]
    )

    # Extract year from 'starred_at' and 'release_published_at'
    star_info["year"] = star_info["starred_at"].dt.year
    release_info["year"] = release_info["release_published_at"].dt.year

    # Define the years of interest
    years_of_interest = [2022, 2023, 2024]
    last_year = 2024

    # Filter star_info for the years of interest
    filtered_stars = star_info[star_info["year"].isin(years_of_interest)]
    stars_per_year = (
        filtered_stars.groupby(["repo_id", "year"]).size().unstack(fill_value=0)
    )
    for year in years_of_interest:
        if year not in stars_per_year.columns:
            stars_per_year[year] = 0
    stars_per_year = stars_per_year[years_of_interest]

    # Check if the number of stars in each of the last 3 years is greater than 0
    stars_per_year["stars_last_3_years"] = stars_per_year.values.tolist()
    stars_per_year["all_years_gt_zero"] = (
        stars_per_year[years_of_interest].gt(0).all(axis=1)
    )

    # Merge the aggregated star information into 'repo_info'
    stars_aggregated = stars_per_year[
        ["stars_last_3_years", "all_years_gt_zero"]
    ].reset_index()
    repo_info = repo_info.merge(stars_aggregated, on="repo_id", how="left")
    repo_info["stars_last_3_years"] = repo_info["stars_last_3_years"].apply(
        lambda x: x if isinstance(x, list) else [0, 0, 0]
    )  # Fill NaN values with appropriate defaults
    repo_info["all_years_gt_zero"] = repo_info["all_years_gt_zero"].fillna(
        False
    )  # Fill NaN values with appropriate defaults

    # Filter release_info for the last year
    releases_last_year = release_info[release_info["year"] == last_year]
    releases_per_repo_last_year = (
        releases_last_year.groupby("repo_id")
        .size()
        .reset_index(name="releases_last_year")
    )

    # Merge the release counts into 'repo_info'
    repo_info = repo_info.merge(releases_per_repo_last_year, on="repo_id", how="left")
    repo_info["releases_last_year"] = (
        repo_info["releases_last_year"].fillna(0).astype(int)
    )  # Fill NaN values with 0 for 'releases_last_year'

    # Define sustainability criteria
    repo_info["is_sustaining"] = (
        (repo_info["status"] != 2)
        & (~repo_info["is_archived"])
        & (repo_info["all_years_gt_zero"] | (repo_info["releases_last_year"] > 0))
    ).astype(int)

    # Reorder columns if necessary
    new_order = [
        "repo_id",
        "repo_owner",
        "repo_name",
        "is_sustaining",
        "is_archived",
        "status",
        "num_stars",
        "stars_last_3_years",
        "releases_last_year",
    ]
    repo_info = repo_info[new_order]

    # Save the updated DataFrame to a CSV file
    repo_info.to_csv(constants.SUSTAINABILITY_CSV_PATH, index=False)

    # Display the updated DataFrame
    print(repo_info.head())


def preprocess_fork_data(teammate):
    # Load datasets
    fork_info = pd.read_csv(constants.FORK_CSV_PATH)
    repo_commit_info = pd.read_csv(constants.REPO_COMMIT_CSV_PATH)
    fork_commit_info = pd.read_csv(constants.FORK_COMMIT_CSV_PATH)
    repo_pr_info = pd.read_csv(constants.REPO_PR_CSV_PATH)
    fork_pr_info = pd.read_csv(constants.FORK_PR_CSV_PATH)

    # Mark the repo commits with fork information
    repo_commit_info["commit_author_id"] = repo_commit_info["commit_author_id"].astype(
        str
    )
    fork_info["fork_owner_id"] = fork_info["fork_owner_id"].astype(str)

    repo_commit_with_fork_df = pd.merge(
        repo_commit_info,
        fork_info[["repo_id", "fork_id", "fork_owner", "fork_name", "fork_owner_id"]],
        left_on=["commit_author_id", "repo_id"],
        right_on=["fork_owner_id", "repo_id"],
        how="left",
    ).assign(is_in_main_repo=True)

    # Count the number of fork_id is NA and drop thoes rows
    nan_count = repo_commit_with_fork_df["fork_id"].isna().sum()
    print(f"❗ Number of rows in repo_commit with NaN fork_id: {nan_count}!")
    repo_commit_with_fork_df = repo_commit_with_fork_df.dropna(subset=["fork_id"])

    # Select and reorder the columns
    repo_commit_with_fork_df = repo_commit_with_fork_df[
        [
            "repo_id",
            "fork_id",
            "fork_owner",
            "fork_name",
            "commit_sha",
            "commit_author",
            "commit_author_id",
            "commit_size",
            "commit_created_at",
            "commit_pushed_at",
            "is_in_main_repo",
        ]
    ]

    # Merge the fork commits with the repo commits
    fork_commit_info["commit_size"] = 0
    fork_commit_info["is_in_main_repo"] = False
    commit_df = pd.concat([repo_commit_with_fork_df, fork_commit_info]).drop_duplicates(
        subset="commit_sha", keep="first"
    )

    # Merge commits with PR information
    # Convert string representations of lists to actual lists, if necessary
    def safe_literal_eval(val):
        try:
            if pd.isna(val):
                return np.nan  # or return an empty list: []
            return ast.literal_eval(val)
        except (ValueError, SyntaxError):
            return val

    if isinstance(repo_pr_info["pr_associated_commits"].iloc[0], str):
        repo_pr_info["pr_associated_commits"] = repo_pr_info[
            "pr_associated_commits"
        ].apply(safe_literal_eval)

    # Explode the 'pr_associated_commits' column
    repo_pr_info_exploded = repo_pr_info.explode("pr_associated_commits")

    commit_with_pr_df = pd.merge(
        commit_df,
        repo_pr_info_exploded[
            [
                "pr_id",
                "pr_associated_commits",
                "pr_state",
                "pr_created_at",
                "pr_merged_at",
                "pr_closed_at",
                "pr_review_comments",
            ]
        ],
        how="left",
        left_on="commit_sha",
        right_on="pr_associated_commits",
    )

    # Select and rename the columns
    commit_with_pr_df = commit_with_pr_df[
        [
            "repo_id",
            "fork_id",
            "fork_owner",
            "fork_name",
            "commit_sha",
            "commit_size",
            "commit_created_at",
            "commit_pushed_at",
            "is_in_main_repo",
            "pr_id",
            "pr_state",
            "pr_created_at",
            "pr_merged_at",
            "pr_closed_at",
            "pr_review_comments",
        ]
    ].rename(
        columns={
            "repo_id_x": "repo_id",
            "is_in_main_repo": "commit_is_in_main_repo",
            "pr_id": "commit_related_pr_id",
            "pr_state": "commit_related_pr_state",
            "pr_created_at": "commit_related_pr_created_at",
            "pr_merged_at": "commit_related_pr_merged_at",
            "pr_closed_at": "commit_related_pr_closed_at",
            "pr_review_comments": "commit_related_pr_review_comments",
        }
    )

    # Merge repo information
    if teammate is not None:
        fork_info = fork_info[fork_info["teammate"] == teammate]
    final_df = pd.merge(
        fork_info,
        commit_with_pr_df[
            [
                "fork_id",
                "commit_sha",
                "commit_size",
                "commit_created_at",
                "commit_pushed_at",
                "commit_is_in_main_repo",
                "commit_related_pr_id",
                "commit_related_pr_state",
                "commit_related_pr_created_at",
                "commit_related_pr_merged_at",
                "commit_related_pr_closed_at",
                "commit_related_pr_review_comments",
            ]
        ],
        on="fork_id",
        how="left",
    )

    # Select and reorder the columns
    final_df = final_df[
        [
            "repo_id",
            "repo_owner",
            "repo_name",
            "fork_id",
            "fork_owner",
            "fork_name",
            "fork_created_at",
            "commit_sha",
            "commit_size",
            "commit_created_at",
            "commit_pushed_at",
            "commit_is_in_main_repo",
            "commit_related_pr_id",
            "commit_related_pr_state",
            "commit_related_pr_created_at",
            "commit_related_pr_merged_at",
            "commit_related_pr_closed_at",
            "commit_related_pr_review_comments",
        ]
    ]

    # Merge 'has_more_than_two_pr' information
    final_df = pd.merge(
        final_df,
        fork_pr_info[["fork_id", "has_more_than_two_pr"]],
        on="fork_id",
        how="left",
    )

    # Label each commit in the fork data
    valid_commits = final_df["commit_sha"].notna()

    def label_commit(row):
        if pd.notna(row["commit_related_pr_id"]) or row.get(
            "commit_is_in_main_repo", False
        ):
            if row.get("commit_is_in_main_repo", False):
                return "merged"
            else:
                return "not merged"
        else:
            return "not contributed back"

    final_df.loc[valid_commits, "commit_label"] = final_df.loc[valid_commits].apply(
        label_commit, axis=1
    )

    # Create boolean columns for each commit label
    final_df["is_merged"] = final_df["commit_label"] == "merged"
    final_df["is_not_merged"] = final_df["commit_label"] == "not merged"
    final_df["not_contributed_back"] = (
        final_df["commit_label"] == "not contributed back"
    )

    # Group by 'fork_id' to aggregate commit information
    fork_grouped = (
        final_df.groupby("fork_id")
        .agg(
            commits_merged=("is_merged", "sum"),
            commits_not_merged=("is_not_merged", "sum"),
            commits_not_contributed_back=("not_contributed_back", "sum"),
            fork_name=("fork_name", "first"),
            repo_name=("repo_name", "first"),
            has_more_than_two_pr=("has_more_than_two_pr", "first"),
        )
        .reset_index()
    )

    # Determine if a fork has contributed back
    fork_grouped["contributed_back_fork"] = (fork_grouped["commits_merged"] > 0) | (
        fork_grouped["commits_not_merged"] > 0
    )

    # Determine if a fork is a hard fork
    fork_grouped["hard_fork"] = fork_grouped["has_more_than_two_pr"] | (
        (fork_grouped["commits_not_contributed_back"] >= 100)
        & (fork_grouped["fork_name"] != fork_grouped["repo_name"])
    )

    # Identify inactive forks
    fork_grouped["inactive_fork"] = (
        (fork_grouped["commits_merged"] == 0)
        & (fork_grouped["commits_not_merged"] == 0)
        & (fork_grouped["commits_not_contributed_back"] == 0)
    )

    # Merge the fork-level classifications back into the original fork_data
    final_df = pd.merge(
        final_df,
        fork_grouped[
            ["fork_id", "contributed_back_fork", "hard_fork", "inactive_fork"]
        ],
        on="fork_id",
        how="left",
    )

    # Save the final DataFrame to a CSV file
    final_df.to_csv(constants.REPO_FORK_COMMIT_PR_CSV_PATH, index=False)

    # Display the final DataFrame
    print(final_df.head())


def preprocess_final_data(teammate):
    # Load the CSV files into DataFrames
    repo_data = pd.read_csv(constants.REPO_CSV_PATH)
    fork_data = pd.read_csv(constants.REPO_FORK_COMMIT_PR_CSV_PATH)
    sustainability_data = pd.read_csv(constants.SUSTAINABILITY_CSV_PATH)

    # Filter repo_data for the specific teammate
    if teammate is not None:
        repo_data = repo_data[repo_data["teammate"] == teammate]

    # Convert 'created_at' to datetime and calculate 'project_age'
    repo_data["created_at"] = pd.to_datetime(repo_data["created_at"], utc=True)
    current_date = pd.Timestamp.now(tz="UTC")
    repo_data["project_age"] = (current_date - repo_data["created_at"]).dt.days / 365

    # Select relevant columns
    repo_info = repo_data[
        ["repo_id", "repo_owner", "repo_name", "project_age", "project_size"]
    ]
    
    # Remove duplicate forks within each repository
    fork_data_unique = fork_data.drop_duplicates(subset=["repo_id", "fork_id"])

    # Calculate total number of forks for each repo
    total_forks = (
        fork_data_unique.groupby("repo_id").size().reset_index(name="total_forks_count")
    )

    # Calculate annual number of forks for each repo and store in a list
    # Ensure 'fork_created_at' is in datetime format and extract the year
    fork_data_unique["fork_created_at"] = pd.to_datetime(
        fork_data_unique["fork_created_at"], utc=True
    )
    fork_data_unique["year"] = fork_data_unique["fork_created_at"].dt.year

    # Filter for the years 2015 to 2024
    fork_data_unique = fork_data_unique[(fork_data_unique["year"] >= 2015) & (fork_data_unique["year"] <= 2024)]

    # Create a DataFrame with all combinations of repo_id and years 2015-2024
    repo_ids = fork_data["repo_id"].unique()
    years = range(2015, 2025)
    all_combinations = pd.MultiIndex.from_product(
        [repo_ids, years], names=["repo_id", "year"]
    ).to_frame(index=False)

    # Group by 'repo_id' and 'year' to count the number of forks
    annual_forks = (
        fork_data_unique.groupby(["repo_id", "year"]).size().reset_index(name="num_forks")
    )

    # Merge the complete combinations with the actual fork counts
    complete_annual_forks = pd.merge(
        all_combinations, annual_forks, on=["repo_id", "year"], how="left"
    ).fillna(0)

    # Ensure 'num_forks' is of integer type
    complete_annual_forks["num_forks"] = complete_annual_forks["num_forks"].astype(int)

    # Aggregate the 'num_forks' into a list for each 'repo_id'
    annual_forks_list = (
        complete_annual_forks.groupby("repo_id")["num_forks"]
        .apply(list)
        .reset_index(name="annual_forks_list")
    )

    # Merge repo_info with total_forks and annual_forks_list
    merged_df = pd.merge(repo_info, total_forks, on="repo_id", how="left")
    merged_df = pd.merge(merged_df, annual_forks_list, on="repo_id", how="left")

        # Ensure 'commit_pushed_at' is in datetime format
    fork_data["commit_pushed_at"] = pd.to_datetime(
        fork_data["commit_pushed_at"], utc=True
    )

    # Define the end date for the analysis
    end_date = pd.Timestamp(datetime(2025, 1, 31), tz="UTC")

    # Generate custom time intervals (February 1st to January 31st of the next year) for the last 10 years
    intervals = []
    for i in range(10):
        start = end_date - timedelta(days=365 * (i + 1)) + timedelta(days=1)
        end = end_date - timedelta(days=365 * i)
        # Convert to pandas.Timestamp
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        intervals.append(pd.Interval(left=start_ts, right=end_ts, closed="both"))

    # Reverse intervals to start from the oldest to the most recent
    intervals = intervals[::-1]

    # Function to assign each commit to an interval
    def assign_interval(commit_date):
        for idx, interval in enumerate(intervals):
            if commit_date in interval:
                return idx
        return None

    # Assign intervals to commits
    fork_data["interval_index"] = fork_data["commit_pushed_at"].apply(assign_interval)

    # Filter out commits that don't fall into any interval
    fork_data = fork_data.dropna(subset=["interval_index"])

    # Aggregate commit information at the repo level
    repo_grouped = (
        fork_data.groupby("repo_id")
        .agg(
            contributed_back_forks_count=("contributed_back_fork", "sum"),
            hard_forks_count=("hard_fork", "sum"),
            inactive_forks_count=("inactive_fork", "sum"),
            merged_commits_count=("is_merged", "sum"),
            #merged_commits_size=(
            #    "commit_size",
            #    lambda x: x[fork_data["is_merged"]].sum(),
            #),
            not_merged_commits_count=("is_not_merged", "sum"),
            not_contributed_back_commits_count=("not_contributed_back", "sum"),
        )
        .reset_index()
        .fillna(0) # Fill NaN values with 0
    )

    # Merge with the main DataFrame
    merged_df = pd.merge(merged_df, repo_grouped, on="repo_id", how="left").fillna(0)

    # Group by 'repo_id' and 'interval_index' to count commits in each category
    commit_counts = (
        fork_data.groupby(["repo_id", "interval_index"])
        .agg(
            num_merged_commits=("is_merged", "sum"),
            num_not_merged_commits=("is_not_merged", "sum"),
            num_not_contributed_back_commits=("not_contributed_back", "sum"),
        )
        .reset_index()
        .fillna(0) # Fill NaN values with 0
    )

    # Convert the commit count columns to integers
    commit_counts[
        [
            "num_merged_commits",
            "num_not_merged_commits",
            "num_not_contributed_back_commits",
        ]
    ] = commit_counts[
        [
            "num_merged_commits",
            "num_not_merged_commits",
            "num_not_contributed_back_commits",
        ]
    ].astype(
        int
    )

    # Pivot the data to have intervals as columns
    commit_counts_pivot = commit_counts.pivot(
        index="repo_id",
        columns="interval_index",
        values=[
            "num_merged_commits",
            "num_not_merged_commits",
            "num_not_contributed_back_commits",
        ],
    ).fillna(0)

    # Function to convert pivoted columns to lists
    def pivot_to_list(df, metric):
        return df[metric].apply(lambda row: row.astype(int).tolist(), axis=1)

    # Create DataFrame to hold the lists
    commit_counts_list = pd.DataFrame(
        {
            "repo_id": commit_counts_pivot.index,
            "merged_commits_list": pivot_to_list(
                commit_counts_pivot, "num_merged_commits"
            ),
            "not_merged_commits_list": pivot_to_list(
                commit_counts_pivot, "num_not_merged_commits"
            ),
            "not_contributed_back_commits_list": pivot_to_list(
                commit_counts_pivot, "num_not_contributed_back_commits"
            ),
        }
    ).reset_index(drop=True)

    # Merge the annual commit lists into the main DataFrame
    merged_df = pd.merge(merged_df, commit_counts_list, on="repo_id", how="left")

    # Create a list of ten 0s
    default_list = [0] * 10
    # Replace empty lists with a list of ten 0s
    for col in ["merged_commits_list", "not_merged_commits_list", "not_contributed_back_commits_list"]:
        merged_df[col] = merged_df[col].apply(
            lambda x: default_list if (isinstance(x, float) and np.isnan(x)) else x
        )

    # Ensure the relevant columns are in datetime format
    fork_data["commit_related_pr_created_at"] = pd.to_datetime(
        fork_data["commit_related_pr_created_at"], utc=True
    )
    fork_data["commit_related_pr_merged_at"] = pd.to_datetime(
        fork_data["commit_related_pr_merged_at"], utc=True
    )

    # Calculate time taken to merge for merged commits
    fork_data["time_taken_to_merge"] = (
        fork_data["commit_related_pr_merged_at"]
        - fork_data["commit_related_pr_created_at"]
    ).dt.total_seconds() / (60 * 60 * 24)

    # Group by 'repo_id' and calculate the mean time taken to merge
    avg_time_taken_to_merge = (
        fork_data[fork_data["is_merged"]]
        .groupby("repo_id")["time_taken_to_merge"]
        .mean()
        .reset_index()
    )

    # Define a function to check for 'compatibility' in text fields
    def contains_compatibility(text):
        if pd.isna(text):
            return False
        return "compatibility" in text.lower()

    # Apply the function to relevant columns and create a boolean column
    fork_data["has_compatibility_issue"] = fork_data[
        "commit_related_pr_review_comments"
    ].apply(contains_compatibility)

    # Filter for unmerged commits with compatibility issues
    unmerged_with_compatibility_issues = fork_data[
        fork_data["is_not_merged"] & fork_data["has_compatibility_issue"]
    ]

    # Count the number of unmerged commits with compatibility issues per repository
    compatibility_issues_count = (
        unmerged_with_compatibility_issues.groupby("repo_id")
        .size()
        .reset_index(name="compatibility_issues_count")
    )

    # Count the total number of unmerged commits per repository
    total_unmerged_commits = (
        fork_data[fork_data["is_not_merged"]]
        .groupby("repo_id")
        .size()
        .reset_index(name="total_unmerged_commits_count")
    )

    # Merge the counts into a single DataFrame
    compatibility_issues_ratio = pd.merge(
        total_unmerged_commits, compatibility_issues_count, on="repo_id", how="left"
    )

    # Fill NaN values with 0 (in case a repo has no compatibility issues)
    compatibility_issues_ratio["compatibility_issues_count"] = (
        compatibility_issues_ratio["compatibility_issues_count"].fillna(0)
    )

    # Calculate the ratio of compatibility issues
    compatibility_issues_ratio["ratio_of_compatibility_issues"] = (
        compatibility_issues_ratio["compatibility_issues_count"]
        / compatibility_issues_ratio["total_unmerged_commits_count"]
    )

    merged_df = pd.merge(merged_df, avg_time_taken_to_merge, on="repo_id", how="left")
    merged_df["time_taken_to_merge"] = merged_df["time_taken_to_merge"].fillna("Not Apply") # Fill NaN values with "Not Apply"

    merged_df = pd.merge(
        merged_df,
        compatibility_issues_ratio[["repo_id", "ratio_of_compatibility_issues"]],
        on="repo_id",
        how="left",
    )
    merged_df["ratio_of_compatibility_issues"] = merged_df["ratio_of_compatibility_issues"].fillna("Not Apply") # Fill NaN values with "Not Apply"

    final_df = pd.merge(
        merged_df,
        sustainability_data[["repo_id", "is_sustaining"]],
        on="repo_id",
        how="left",
    )

    # Save the final DataFrame to a CSV file
    final_df.to_csv(constants.FINAL_CSV_PATH, index=False)

    # Display the final DataFrame
    print(final_df.head())


def dataget(args):
    """Handles data collection based on the specified case."""
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: No GitHub token provided.")
        exit(1)
    github_api = API(args, token)

    choice_handlers = {
        1: handle_repo_data,
        2: handle_fork_data,
        3: handle_repo_commit_data,
        4: handle_fork_commit_data,
        5: handle_repo_pr_data,
        6: handle_fork_pr_data,
        7: handle_star_data,
        8: handle_release_data,
    }

    handler = choice_handlers.get(args.choice)
    if handler:
        handler(github_api, args.name)
    else:
        print("Error: Invalid choice.")
        exit(1)


def datapre(args):
    """Handles dataset preprocessing (to be implemented)."""
    step_handlers = {
        1: preprocess_sustainability_data,
        2: preprocess_fork_data,
        3: preprocess_final_data,
    }

    handler = step_handlers.get(args.step)
    if handler:
        handler(args.name)
    else:
        print("Error: Invalid step.")
        exit(1)


def datavis(args):
    """Handles dataset visualization (to be implemented)."""
    pass


# main entry point for all scripts
def main():
    parser = argparse.ArgumentParser(
        description="entry point for all scripts releating to Github Fork Research project"
    )
    subparsers = parser.add_subparsers(
        dest="subparser_name", required=True, help="available commands"
    )

    # sub parser for data collection
    data_get = subparsers.add_parser("dataget", help="Get dataset")
    data_get.add_argument(
        "--choice",
        type=int,
        choices=[1, 2, 3, 4, 5, 6, 7, 8],
        help="Specify the data to be collected (1: repo, 2: fork, 3: repo commit, 4: fork commit, 5: repo PR, 6: fork PR; 7: star; 8: release)",
    )
    data_get.add_argument(
        "--name",
        type=str,
        help="Specify the teammate name responsible for the data collection",
    )

    # sub parser for data preprocessing
    data_pre = subparsers.add_parser("datapre", help="Preprocessing of dataset")
    data_pre.add_argument(
        "--step",
        type=int,
        choices=[1, 2, 3],
        help="Specify the step of data preprocessing (1: sustainability, 2: fork, 3: final)",
    )
    data_pre.add_argument(
        "--name",
        type=str,
        help="Specify the teammate name for sustainability data preprocessing",
    )

    # sub parser for dataset analysis
    data_vis = subparsers.add_parser("datavis", help="Visualization of dataset")

    args = parser.parse_args()
    if args.subparser_name == "datavis":
        datavis(args)
    elif args.subparser_name == "datapre":
        datapre(args)
    elif args.subparser_name == "dataget":
        dataget(args)


if __name__ == "__main__":
    main()
