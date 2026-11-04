import os
import subprocess
import shutil

root = r"D:\ScreenGuard"
work_index = os.path.join(r"C:\Users\tejas\AppData\Local\Temp", "git_index_work")
orig_index = os.path.join(root, ".git", "index")

env = os.environ.copy()
env["GIT_INDEX_FILE"] = work_index

# Stage all files
subprocess.run(["git", "add", "-A"], cwd=root, env=env, check=True)

# Commit
commit_msg = "feat: evaluation tab, preflight, honest docs"
subprocess.run(["git", "commit", "-m", commit_msg], cwd=root, env=env, check=True)

# Tag next-4
subprocess.run(["git", "tag", "-f", "next-4"], cwd=root, env=env, check=True)

# Replace repository index with work_index
shutil.copy2(work_index, orig_index)

# Push to origin main and tags
subprocess.run(["git", "push", "origin", "main", "--tags"], cwd=root, check=True)
print("Successfully pushed next-4 to origin main with tags!")
