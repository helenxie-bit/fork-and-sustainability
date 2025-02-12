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


def preprocess_sustainability_data(teammate=None):
    # Load datasets
    repo_info = pd.read_csv(constants.REPO_CSV_PATH)
    project_list = pd.read_csv(constants.PROJECTS_LIST)
    star_info = pd.read_csv(constants.STAR_CSV_PATH)
    release_info = pd.read_csv(constants.RELEASE_CSV_PATH)

    # Merge 'status' from project_list into repo_info
    project_list['listname_lower'] = project_list['listname'].str.lower()
    if teammate is not None:
        repo_info = repo_info[repo_info['teammate'] == teammate]
    repo_info = repo_info.merge(project_list[['listname_lower', 'status']], left_on='repo_name', right_on='listname_lower', how='left')

    # Convert 'starred_at' and 'release_published_at' to datetime
    star_info['starred_at'] = pd.to_datetime(star_info['starred_at'])
    release_info['release_published_at'] = pd.to_datetime(release_info['release_published_at'])

    # Extract year from 'starred_at' and 'release_published_at'
    star_info['year'] = star_info['starred_at'].dt.year
    release_info['year'] = release_info['release_published_at'].dt.year

    # Define the years of interest
    years_of_interest = [2022, 2023, 2024]
    last_year = 2024

    # Filter star_info for the years of interest
    filtered_stars = star_info[star_info['year'].isin(years_of_interest)]
    stars_per_year = filtered_stars.groupby(['repo_id', 'year']).size().unstack(fill_value=0)
    for year in years_of_interest:
        if year not in stars_per_year.columns:
            stars_per_year[year] = 0
    stars_per_year = stars_per_year[years_of_interest]

    # Check if the number of stars in each of the last 3 years is greater than 0
    stars_per_year['stars_last_3_years'] = stars_per_year.values.tolist()
    stars_per_year['all_years_gt_zero'] = stars_per_year[years_of_interest].gt(0).all(axis=1)

    # Merge the aggregated star information into 'repo_info'
    stars_aggregated = stars_per_year[['stars_last_3_years', 'all_years_gt_zero']].reset_index()
    repo_info = repo_info.merge(stars_aggregated, on='repo_id', how='left')
    repo_info['stars_last_3_years'] = repo_info['stars_last_3_years'].apply(lambda x: x if isinstance(x, list) else [0, 0, 0]) # Fill NaN values with appropriate defaults
    repo_info['all_years_gt_zero'] = repo_info['all_years_gt_zero'].fillna(False) # Fill NaN values with appropriate defaults

    # Filter release_info for the last year
    releases_last_year = release_info[release_info['year'] == last_year]
    releases_per_repo_last_year = releases_last_year.groupby('repo_id').size().reset_index(name='releases_last_year')

    # Merge the release counts into 'repo_info'
    repo_info = repo_info.merge(releases_per_repo_last_year, on='repo_id', how='left')
    repo_info['releases_last_year'] = repo_info['releases_last_year'].fillna(0).astype(int) # Fill NaN values with 0 for 'releases_last_year'

    # Define sustainability criteria
    repo_info['is_sustaining'] = (
        (repo_info['status'] != 2) &
        (~repo_info['is_archived']) &
        (repo_info['all_years_gt_zero'] | (repo_info['releases_last_year'] > 0))
    ).astype(int)

    # Reorder columns if necessary
    new_order = [
        'repo_id', 'repo_owner', 'repo_name', 'is_sustaining', 'is_archived', 'status',
        'num_stars', 'stars_last_3_years', 'releases_last_year'
    ]
    repo_info = repo_info[new_order]

    # Save the updated DataFrame to a CSV file
    repo_info.to_csv(constants.SUSTAINABILITY_CSV_PATH, index=False)

    # Display the updated DataFrame
    print(repo_info.head())


def preprocess_fork_data(args):
    pass

def preprocess_final_data(args):
    pass


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


def datapre(args):
    """Handles dataset preprocessing (to be implemented)."""
    preprocess_sustainability_data(args.teammate if args.teammate else None)
    preprocess_fork_data(args)
    preprocess_final_data(args)


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
        choices=[1, 2, 3, 4, 5],
        help="Specify the data to be collected (1: repo, 2: fork, 3: commit, 4: repo PR, 5: fork PR)",
    )
    data_get.add_argument(
        "--teammate",
        type=str,
        help="Specify the teammate responsible for the data collection",
    )

    # sub parser for data preprocessing
    data_pre = subparsers.add_parser(
        "datapre", help="Preprocessing of dataset"
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
