import argparse
from dotenv import load_dotenv
import os
from API.api import API
import pandas as pd
from pprint import pprint
import constants


def check_file_exists(filepath, msg):
    """Helper function to check if a file exists."""
    if not os.path.exists(filepath):
        print(f"Error: {msg}")
        exit(1)


def datavis(args):
    """Handles dataset visualization (to be implemented)."""
    pass


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


def handle_repo_data(github_api, teammate):
    """Handles repo general information collection."""
    check_file_exists(
        constants.PROJECTS_LIST, f"{constants.PROJECTS_LIST} does not exist."
    )
    df_projects = pd.read_csv(constants.PROJECTS_LIST)

    for project in df_projects["listname"]:
        repo_owner = "apache"
        repo_name = project.strip()  # Remove leading/trailing whitespace
        github_api.get_repo_data(
            repo_owner, repo_name, constants.REPO_CSV_PATH, constants.MISSING_CSV_PATH
        )


def handle_fork_data(github_api, teammate):
    """Handles fork data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)

    for repo_id, repo_owner, repo_name in zip(
        df_repos["repo_id"], df_repos["repo_owner"], df_repos["repo_name"]
    ):
        github_api.get_fork_data(
            repo_id, repo_owner, repo_name, constants.FORK_CSV_PATH
        )


def handle_commit_data(github_api, teammate):
    """Handles commit data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)
    filter_repos = df_repos[df_repos["teammate"] == teammate]

    check_file_exists(
        constants.FORK_CSV_PATH,
        f"{constants.FORK_CSV_PATH} does not exist. Please run choice 2 first.",
    )
    df_forks = pd.read_csv(constants.FORK_CSV_PATH)
    filter_forks = df_forks[df_forks["teammate"] == teammate]

    # Resume from last processed fork
    resume_log_path = constants.RESUME_LOG_PATH_COMMIT
    last_processed_fork, last_processed_page = resume_from_checkpoint(
        resume_log_path, with_page=True
    )

    for fork_id, fork_owner, fork_name in zip(
        filter_forks["fork_id"], filter_forks["fork_owner"], filter_forks["fork_name"]
    ):
        # Resume processing if interrupted
        if last_processed_fork and str(fork_id) != last_processed_fork:
            continue  # Skip to the last processed fork

        fork_parent_id = df_forks[df_forks["fork_id"] == fork_id][
            "fork_parent_id"
        ].values[0]
        fork_parent_owner = df_forks[df_forks["fork_id"] == fork_id][
            "fork_parent_owner"
        ].values[0]
        fork_parent_name = df_forks[df_forks["fork_id"] == fork_id][
            "fork_parent_name"
        ].values[0]
        default_branch = df_repos[df_repos["repo_id"] == fork_parent_id][
            "default_branch"
        ].values[0]
        github_api.get_commit_data(
            fork_parent_id,
            fork_parent_owner,
            fork_parent_name,
            fork_id,
            fork_owner,
            fork_name,
            default_branch,
            constants.COMMIT_CSV_PATH,
            constants.RESUME_LOG_PATH_COMMIT,
            last_processed_page,
        )

        last_processed_fork = None  # Reset last processed fork
        last_processed_page = None  # Reset last processed page


def handle_repo_pr_data(github_api, teammate):
    """Handles repo PR data collection."""
    check_file_exists(
        constants.REPO_CSV_PATH,
        f"{constants.REPO_CSV_PATH} does not exist. Please run choice 1 first.",
    )
    df_repos = pd.read_csv(constants.REPO_CSV_PATH)
    filter_repos = df_repos[df_repos["teammate"] == teammate]

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
            constants.RESUME_LOG_PATH_REPO_PR,
            last_processed_page,
        )

        last_processed_repo = None  # Reset last processed repo
        last_processed_page = None  # Reset last processed page


def handle_fork_pr_data(github_api, teammate):
    """Handles fork PR data collection."""
    check_file_exists(
        constants.FORK_CSV_PATH,
        f"{constants.FORK_CSV_PATH} does not exist. Please run choice 2 first.",
    )
    df_forks = pd.read_csv(constants.FORK_CSV_PATH)
    filter_forks = df_forks[df_forks["teammate"] == teammate]

    # Resume from last processed fork
    resume_log_path = constants.RESUME_LOG_PATH_FORK_PR
    last_processed_fork = resume_from_checkpoint(resume_log_path, with_page=False)

    for fork_parent_id, fork_id, fork_owner, fork_name in zip(
        filter_forks["fork_parent_id"],
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
        3: handle_commit_data,
        4: handle_repo_pr_data,
        5: handle_fork_pr_data,
    }

    handler = choice_handlers.get(args.choice)
    if handler:
        handler(github_api, args.teammate)
    else:
        print("Error: Invalid choice.")
        exit(1)


# main entry point for all scripts
def main():
    parser = argparse.ArgumentParser(
        description="entry point for all scripts releating to Github Fork Research project"
    )
    subparsers = parser.add_subparsers(
        dest="subparser_name", required=True, help="available commands"
    )

    # sub parser for dataset analysis
    data_vis = subparsers.add_parser("datavis", help="Visualization of dataset")
    data_get = subparsers.add_parser("dataget", help="Get dataset")
    data_get.add_argument(
        "--choice",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Specify the data to be collected (1: repo, 2: fork, 3: commit, 4: repo PR, 5: fork PR)",
    )
    data_get.add_argument(
        "--teammate",
        type=str,
        help="Specify the teammate responsible for the data collection",
    )

    args = parser.parse_args()
    if args.subparser_name == "datavis":
        datavis(args)
    elif args.subparser_name == "dataget":
        dataget(args)


if __name__ == "__main__":
    main()
