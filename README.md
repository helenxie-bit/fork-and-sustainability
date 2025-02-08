## **Data Collection**
This project provides five options for collecting GitHub repository data:

1. **Repository metadata** (repo) ✅ *(Completed)*
2. **Fork information** (fork) ✅ *(Completed)*
3. **Commit history** (commit) ⏳ *(In Progress)*
4. **Pull requests for repositories** (repo PR) ⏳ *(In Progress)*
5. **Pull requests for forks** (fork PR) ⏳ *(In Progress)*

Tasks **3, 4, and 5** are distributed among team members based on the number of forks to ensure a balanced workload.

---

### **Usage Instructions**
#### **1. Generate a GitHub Personal Access Token**
To interact with the GitHub API, you need a **GitHub Personal Access Token**.  
Follow this guide to generate one: [Generate GitHub Token](https://www.geeksforgeeks.org/how-to-generate-personal-access-token-in-github/).

#### **2. Set Up the Environment Variable**
Use the generated token to set the **`GITHUB_TOKEN`** environment variable:

- **Mac/Linux (temporary):**
  ```bash
  export GITHUB_TOKEN="your_personal_access_token"
  ```

- **Windows (PowerShell):**
  ```powershell
  $env:GITHUB_TOKEN="your_personal_access_token"
  ```

For a **permanent setup**, add the export command to `~/.bashrc` or `~/.zshrc` (Linux/macOS) or set it in system environment variables (Windows).

---

#### **3. Run the Data Collection Command**
Use the following command to collect data:

```bash
python CLI.py dataget --choice <3-5> --teammate <your_name>
```

Replace **`<3-5>`** with the desired data type:
- `3` → Commit information of forks
- `4` → Repository pull requests
- `5` → Fork pull requests  

Replace **`<your_name>`** with your assigned name (**helen, joseph, junlong, simmon, sophie**).

---

#### **4. Resuming Data Collection**
- If the process **hits GitHub API rate limits**, it will **pause (sleep)** and automatically resume from the last checkpoint after a certain period.
- If you **manually interrupt** the process and need to resume, simply **rerun the same command**—**no additional configuration is required**.

---
