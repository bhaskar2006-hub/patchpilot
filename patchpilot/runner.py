"""Execution runner for test suites and sandbox validation."""

import subprocess
import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class TestResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    passed: bool


class TestRunner:
    """Executes arbitrary test commands in the target workspace."""

    @staticmethod
    def run(command: str, cwd: Optional[str] = None, timeout: int = 180) -> TestResult:
        import os
        import sys
        start_time = time.time()
        env = os.environ.copy()
        python_bin_dir = os.path.dirname(sys.executable)
        if python_bin_dir:
            env["PATH"] = f"{python_bin_dir}:{env.get('PATH', '')}"

        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            duration = time.time() - start_time
            passed = (process.returncode == 0)
            return TestResult(
                command=command,
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration_seconds=duration,
                passed=passed,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return TestResult(
                command=command,
                exit_code=124,
                stdout=e.stdout or "",
                stderr=f"Test timed out after {timeout} seconds.",
                duration_seconds=duration,
                passed=False,
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                command=command,
                exit_code=1,
                stdout="",
                stderr=f"Failed to execute command: {str(e)}",
                duration_seconds=duration,
                passed=False,
            )

    @staticmethod
    def detect_test_command(cwd: Optional[str] = None) -> str:
        """Autodetects the test runner command for the current directory."""
        import os
        path = cwd or os.getcwd()
        
        # Python
        if os.path.exists(os.path.join(path, "pytest.ini")) or os.path.exists(os.path.join(path, "tests")):
            return "pytest"
        if os.path.exists(os.path.join(path, "pyproject.toml")):
            return "pytest"
            
        # Node / JS / TS
        if os.path.exists(os.path.join(path, "package.json")):
            return "npm test"
            
        # Rust
        if os.path.exists(os.path.join(path, "Cargo.toml")):
            return "cargo test"
            
        # Go
        if os.path.exists(os.path.join(path, "go.mod")):
            return "go test ./..."
            
        return "pytest"
