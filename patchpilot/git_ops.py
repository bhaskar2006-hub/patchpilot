"""Git operations, safe backup/rollback, diff formatting, and conventional commit generation."""

import os
import shutil
import subprocess
from typing import Optional, Dict


class GitOps:
    """Safely handles file backups, rollbacks, git diffs, and commits."""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getcwd()
        self._backups: Dict[str, str] = {}

    def backup_file(self, file_path: str):
        """Keep an in-memory backup of the original file contents for zero-risk rollback."""
        full_path = os.path.join(self.repo_path, file_path) if not os.path.isabs(file_path) else file_path
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                self._backups[file_path] = f.read()

    def rollback(self):
        """Restore all backed-up files to their exact original state."""
        for file_path, content in self._backups.items():
            full_path = os.path.join(self.repo_path, file_path) if not os.path.isabs(file_path) else file_path
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
        self._backups.clear()

    def apply_file_content(self, file_path: str, new_content: str):
        """Write new content to file after taking a backup."""
        if file_path not in self._backups:
            self.backup_file(file_path)
            
        full_path = os.path.join(self.repo_path, file_path) if not os.path.isabs(file_path) else file_path
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def get_diff(self, file_path: Optional[str] = None) -> str:
        """Returns the current git diff for a specific file or the entire repo."""
        try:
            cmd = ["git", "diff", "--color=never"]
            if file_path:
                cmd.append(file_path)
            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            return result.stdout
        except Exception:
            return ""

    def commit_fix(self, message: str, files: Optional[list] = None) -> bool:
        """Stage and commit the verified fix."""
        try:
            stage_cmd = ["git", "add"] + (files if files else ["-u"])
            subprocess.run(stage_cmd, cwd=self.repo_path, check=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo_path, check=True)
            return True
        except Exception:
            return False

    def is_git_repo(self) -> bool:
        return os.path.exists(os.path.join(self.repo_path, ".git"))
