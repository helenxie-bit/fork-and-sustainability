import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset

class ForkDataset(Dataset):
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def __len__(self):
        return len(self.dataframe)
    
    def formatting(self, data):
        
        # irrelevant data: repo_id, repo_owner, repo_name(?)
        
        # relevant data:
        # project age
        project_age = data['project_age'] / 15 # crush down to approximately 0-1

        # project size
        project_size = data['project_size'] / 250000

        # fork count
        fork_count = data['total_forks_count'] / 10000

        # fork list by year
        fork_list = [float(fork) / 2500 for fork in data['annual_forks_list'].strip('[]').split(',')]

        # contriduted back forks
        contributed_back_forks = data['contributed_back_forks_count'] / 50000

        # hard forks count
        hard_forks = data['hard_forks_count'] / 50000

        # input data formatting

        input_data = [project_age, project_size, fork_count] + fork_list + [contributed_back_forks, hard_forks]

        # label
        label = data["is_sustaining"]

        return torch.tensor(input_data).to(torch.float32), torch.tensor(label)

    def __getitem__(self, idx):
        row = self.dataframe.iloc[idx]
        formatted_data, label = self.formatting(row)
        return formatted_data, label