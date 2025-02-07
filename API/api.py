import os
import requests

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
            repo_id = repo_json['id']
            repo_owner = repo_json['owner']['login']
            return repo_response
        except Exception as e:
            print(f"Error: Unable to fetch '{owner}/{repo}'. Status code: {repo_response.status_code}")
            print(f"Response: {repo_response.text}")
            return

        
