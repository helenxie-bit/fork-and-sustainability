## **Data Collection**
This project collects eight kinds of GitHub repository data:

1. **Repo information** ✅ *(Completed)*
2. **Fork information** ✅ *(Completed)*
3. **Repo commit information** ✅ *(Completed)*
4. **Fork commit information** ✅ *(Completed)*
5. **Repo PR information** ✅ *(Completed)*
6. **Fork PR information** ✅ *(Completed)*
7. **Star information** ✅ *(Completed)*
8. **Release information** ✅ *(Completed)*

### **Usage Instructions**
#### **1. Clone the Repo to Local**
```bash
git clone https://github.com/helenxie-bit/fork-and-sustainability.git
```

#### **2. Generate a GitHub Personal Access Token**
To interact with the GitHub API, you need a GitHub Personal Access Token. Follow this guide to generate one: [Generate GitHub Token](https://www.geeksforgeeks.org/how-to-generate-personal-access-token-in-github/).

#### **3. Set Up the Environment Variable**
Use the generated token to set the `GITHUB_TOKEN` environment variable:

- **Mac/Linux (temporary):**
  ```bash
  export GITHUB_TOKEN="your_personal_access_token"
  ```

- **Windows (PowerShell):**
  ```powershell
  $env:GITHUB_TOKEN="your_personal_access_token"
  ```

For a permanent setup, add the export command to `~/.bashrc` or `~/.zshrc` (Linux/macOS) or set it in system environment variables (Windows).

#### **4. Run the Data Collection Command**
Use the following command to collect data:

```bash
python CLI.py dataget --choice <3-6> --name <teammate name>
```

**Note:**
- If the process hits GitHub API rate limits, it will pause (sleep) and automatically resume from the last checkpoint after a certain period.
- If you manually interrupt the process and need to resume, simply rerun the same command—no additional configuration is required.


## **Data Preprocessing**
Use the following command to preprocess data:

```bash
python CLI.py datapre --step <1-3>
```

Based on the collected data, we constructed measures for fork-related factors and sustainability labels, as summarized in the following table:

| **Type** | **Measure** | **Explanation** |
|----------|------------|----------------|
| **General** | **Project Age** | Duration from project creation date to current date. |
|  | **Project Size** | Total size of the project repository (in KB). |
| **Fork-Related Factors (RQ1)** | **Total Forks** | Total number of forks. |
|  | **Annual Forks Growth Rate** | Percentage of change of number of forks created per year. |
| **Fork-Related Factors (RQ2)** | **Contributed Back Forks** | Number of forks that made commits back. |
|  | **Hard Forks** | Number of forks meeting criteria: (1) Over 2 pull requests; or (2) Over 100 unmerged commits with project name changed. |
|  | **Inactive Forks** | Number of forks with no commits. |
| **Fork-Related Factors (RQ3)** | **Merged Commits** | Total number of merged commits. |
|  | **Annual Merged Commits Growth Rate** | Percentage of change of number of merged commits pushed per year. |
|  | **Unmerged Commits** | Total number of unmerged commits. |
|  | **Annual Unmerged Commits Growth Rate** | Percentage of change of number of unmerged commits pushed per year. |
|  | **Fork-Only Commits** | Total number of commits exclusive to forks. |
|  | **Annual Fork-Only Commits Growth Rate** | Percentage of change of number of commits exclusive to forks per year. |
| **Fork-Related Factors (RQ4)** | **Average Time Taken to Merge** | Average time from pull request creation to merge. |
| **Fork-Related Factors (RQ5)** | **Ratio of Compatibility Issues** | Proportion of unmerged commits with review comments mentioning "compatibility" issues. |
| **Sustainability** | **Is Sustaining Or Not** | Defined by: (1) Project is not "retired"; (2) GitHub repository is not archived; (3) Consistent activity, shown by stars (2022-2024) or releases in 2024. |


## **Data Analysis**
Please refer to the notebooks in this repository.
