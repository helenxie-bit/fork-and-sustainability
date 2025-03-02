## **Data Collection**
This project provides five options for collecting GitHub repository data:

1. **Repo information** ✅ *(Completed)*
2. **Fork information** ✅ *(Completed)*
3. **Repo commit information** ⏳ *(In Progress)*
4. **Fork commit information** ⏳ *(In Progress)*
5. **Repo PR information** ⏳ *(In Progress)*
6. **Fork PR information** ⏳ *(In Progress)*
7. **Star information** ✅ *(Completed)*
8. **Release information** ✅ *(Completed)*

Tasks **3, 4, 5, and 6** are distributed among team members based on the number of forks to ensure a balanced workload.

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
python CLI.py dataget --choice <3-6> --name <your_name>
```

Replace `<3-6>` with the desired data type.
Replace `<your_name>` with your assigned name (**helen, joseph, junlong, simmon, sophie**).

**Note:**
- If the process hits GitHub API rate limits, it will pause (sleep) and automatically resume from the last checkpoint after a certain period.
- If you manually interrupt the process and need to resume, simply rerun the same command—no additional configuration is required.
