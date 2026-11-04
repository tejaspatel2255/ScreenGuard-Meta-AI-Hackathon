import os
import subprocess
import shutil

root = r"D:\ScreenGuard"
git_dir = os.path.join(root, ".git")
orig_index = os.path.join(git_dir, "index")
work_index = os.path.join(r"C:\Users\tejas\AppData\Local\Temp", "git_index_work")

shutil.copy2(orig_index, work_index)
env = os.environ.copy()
env["GIT_INDEX_FILE"] = work_index

# Restore eval/results
subprocess.run(["git", "checkout", "HEAD", "--", "eval/results"], cwd=root, env=env, check=True)

# Add all modified files
subprocess.run(["git", "add", "-A"], cwd=root, env=env, check=True)

# Status
res = subprocess.run(["git", "status"], cwd=root, env=env, capture_output=True, text=True)
print("Git Status:")
print(res.stdout)
