import requests
import pandas as pd
import os

# GitHub API Token
# GitHub personal acess token tutorial: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# Read project list from CSV
project_list_path = "projects_list.csv"
if not os.path.exists(project_list_path):
    print(f"Error: {project_list_path} does not exist.")
    exit(1)
df_projects = pd.read_csv(project_list_path)

# Define output CSV file path
repo_csv_path = "data/repo_info.csv"
missing_csv_path = "data/missing_repos.csv"
repo_file_exists = os.path.exists(repo_csv_path) # Check if the file already exists
missing_file_exists = os.path.exists(missing_csv_path) # Check if the file already exists

# Iterate through each project in the list
for project in df_projects["listname"]:
    MAIN_OWNER = "apache"
    MAIN_REPO = project.strip() # Remove leading/trailing whitespace

    # Get general repository information
    repo_url = f"https://api.github.com/repos/{MAIN_OWNER}/{MAIN_REPO}"
    repo_response = requests.get(repo_url, headers=HEADERS)

    # Check for API errors
    if repo_response.status_code == 404:
        print(f"Error: Repository {MAIN_OWNER}/{MAIN_REPO} not found. Skipping...")

        # Convert to DataFrame and write to missing_repos.csv immediately
        df_missing = pd.DataFrame([{"repo_name": MAIN_REPO}])
        df_missing.to_csv(missing_csv_path, mode="a", header=not missing_file_exists, index=False)
        missing_file_exists = True # Update file existence flag after first write

        continue

    elif repo_response.status_code != 200:
        print(f"Error: Unable to fetch '{MAIN_OWNER}/{MAIN_REPO}'. Status code: {repo_response.status_code}")
        print(f"Response: {repo_response.text}")
        exit(1)

    # Parse response JSON and extract repository information
    repo_data = repo_response.json()
    repo_info = {
        "repo_id": repo_data['id'],
        "repo_owner": repo_data['owner']['login'],
        "repo_name": repo_data['name'],
        "created_at": repo_data['created_at'],
        "project_size": repo_data['size'],
        "num_forks": repo_data['forks_count'],
        "default_branch": repo_data['default_branch'],
        "last_update": repo_data['updated_at'],
        "repo_url": repo_data['html_url']
    }

    # Conver to DataFrame and save to CSV
    df = pd.DataFrame([repo_info])
    df.to_csv(repo_csv_path, mode="a", header=not repo_file_exists, index=False)
    repo_file_exists = True # Update the flag after the first write

    print(f"Repository {MAIN_OWNER}/{MAIN_REPO} information saved to {repo_csv_path}")
