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
commit_msg = "fix(replay): maintain stable frame and index refs to prevent timer stalls"
subprocess.run(["git", "commit", "-m", commit_msg], cwd=root, env=env, check=True)

# Replace repository index with work_index
shutil.copy2(work_index, orig_index)

# Push to origin main
subprocess.run(["git", "push", "origin", "main"], cwd=root, check=True)
print("Pushed replay fix to origin main!")
