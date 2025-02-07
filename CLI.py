import argparse
from dotenv import load_dotenv
import os
from API.api import API
import pandas as pd
from pprint import pprint

def datavis(args):
    pass

def API_check(args):
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: No GitHub token provided.")
        exit(1)
    github_api = API(args, token)

    df_projects = pd.read_csv("projects_list.csv")
    
    for project in [df_projects["listname"][0]]:
        owner = "apache"
        repo = project.strip()
        response = github_api.pull_repo(owner, repo)
        pprint(response.json())

# main entry point for all scripts
def main():
    parser = argparse.ArgumentParser(description='entry point for all scripts releating to Github Fork Research project')
    subparsers = parser.add_subparsers(dest='subparser_name', required=True, help='available commands')

    # sub parser for dataset analysis
    data_vis = subparsers.add_parser('datavis', help='Visualization of dataset')
    data_get = subparsers.add_parser('dataget', help='Get dataset')

    args = parser.parse_args()
    if args.subparser_name == 'datavis':
        datavis(args)
    elif args.subparser_name == 'dataget':
        API_check(args)


if __name__ == '__main__':
    main()