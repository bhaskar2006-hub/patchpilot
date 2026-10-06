"""Core engine orchestrating the test-diagnose-patch-verify autonomous healing loop."""

import os
from dataclasses import dataclass
from typing import List, Optional, Callable

from patchpilot.parser import TestLogParser, TestFailure
from patchpilot.llm.client import LocalSLMClient, LLMResponse
from patchpilot.llm.prompts import PromptBuilder
from patchpilot.runner import TestRunner, TestResult
from patchpilot.git_ops import GitOps


@dataclass
class HealAttempt:
    attempt_number: int
    failure: TestFailure
    patch_diff: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class HealResult:
    initial_passed: bool
    healed: bool
    attempts: List[HealAttempt]
    final_diff: str
    model_used: str
    total_duration: float
    message: str


class SelfHealingEngine:
    """Automates diagnosis and repair of test failures using local open-weight SLMs."""

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        model: Optional[str] = None,
        max_attempts: int = 3,
        auto_commit: bool = False,
        llm_url: Optional[str] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.max_attempts = max_attempts
        self.auto_commit = auto_commit
        self.on_status = on_status or (lambda s: None)
        self.client = LocalSLMClient(model=model, base_url=llm_url)
        self.git = GitOps(repo_path=self.workspace_dir)

    def _notify(self, message: str):
        self.on_status(message)

    def heal(self, test_cmd: Optional[str] = None) -> HealResult:
        """Run test command, diagnose any failure, and attempt self-repair."""
        cmd = test_cmd or TestRunner.detect_test_command(self.workspace_dir)
        self._notify(f"🚀 Running test suite: `{cmd}`")
        
        initial_result = TestRunner.run(cmd, cwd=self.workspace_dir)
        if initial_result.passed:
            self._notify("✅ Test suite is already passing cleanly! No repair needed.")
            return HealResult(
                initial_passed=True,
                healed=True,
                attempts=[],
                final_diff="",
                model_used=self.client.model,
                total_duration=initial_result.duration_seconds,
                message="All tests passed on initial run.",
            )

        self._notify(f"❌ Test suite failed with exit code {initial_result.exit_code}. Analyzing failure...")
        
        combined_logs = f"{initial_result.stdout}\n{initial_result.stderr}"
        failures = TestLogParser.parse(combined_logs)

        if not failures:
            self._notify("⚠️ Could not parse structured test failures from log output.")
            return HealResult(
                initial_passed=False,
                healed=False,
                attempts=[],
                final_diff="",
                model_used=self.client.model,
                total_duration=initial_result.duration_seconds,
                message="Failed to parse test failure logs.",
            )

        self._notify(f"🔍 Found {len(failures)} test failure(s). Starting local SLM repair loop ({self.client.model})...")

        attempts: List[HealAttempt] = []
        target_failure = failures[0]
        file_path = target_failure.file_path

        # Resolve full path
        full_file_path = os.path.join(self.workspace_dir, file_path) if not os.path.isabs(file_path) else file_path
        
        # If file doesn't exist directly (e.g. relative path mismatch), search workspace
        if not os.path.exists(full_file_path):
            basename = os.path.basename(file_path)
            for root, _, files in os.walk(self.workspace_dir):
                if basename in files and not any(ignored in root for ignored in (".git", ".venv", "node_modules", "__pycache__")):
                    full_file_path = os.path.join(root, basename)
                    file_path = os.path.relpath(full_file_path, self.workspace_dir)
                    break

        if not os.path.exists(full_file_path):
            self._notify(f"⚠️ Target file `{file_path}` not found in workspace.")
            return HealResult(
                initial_passed=False,
                healed=False,
                attempts=[],
                final_diff="",
                model_used=self.client.model,
                total_duration=initial_result.duration_seconds,
                message=f"Target file {file_path} not found.",
            )

        with open(full_file_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        # Take backup
        self.git.backup_file(file_path)

        last_error = None
        for attempt_idx in range(1, self.max_attempts + 1):
            self._notify(f"🤖 [Attempt {attempt_idx}/{self.max_attempts}] Prompting {self.client.model} for surgical fix...")
            
            prompt = PromptBuilder.build_repair_prompt(
                file_path=file_path,
                file_content=original_code,
                test_name=target_failure.test_name,
                error_message=target_failure.error_message,
                stack_trace=target_failure.stack_trace,
                line_number=target_failure.line_number,
                previous_attempt_error=last_error,
            )

            try:
                llm_resp = self.client.generate(prompt, system_prompt=PromptBuilder.SYSTEM_PROMPT)
                repaired_code = PromptBuilder.extract_code_block(llm_resp.content)
                
                if not repaired_code:
                    self._notify(f"⚠️ SLM output did not contain valid codeblock.")
                    continue

                # Apply candidate fix
                self.git.apply_file_content(file_path, repaired_code)
                diff = self.git.get_diff(file_path)

                self._notify("🧪 Verifying patch with test suite...")
                verify_result = TestRunner.run(cmd, cwd=self.workspace_dir)

                if verify_result.passed:
                    self._notify("🎉 PATCH VERIFIED! All tests passing!")
                    attempts.append(HealAttempt(
                        attempt_number=attempt_idx,
                        failure=target_failure,
                        patch_diff=diff,
                        success=True,
                    ))

                    if self.auto_commit and self.git.is_git_repo():
                        commit_msg = f"fix(ci): self-heal {target_failure.test_name} in {file_path}\n\nGenerated by PatchPilot ({self.client.model})"
                        self.git.commit_fix(commit_msg, files=[file_path])
                        self._notify(f"💾 Committed fix to git: {commit_msg.splitlines()[0]}")

                    return HealResult(
                        initial_passed=False,
                        healed=True,
                        attempts=attempts,
                        final_diff=diff,
                        model_used=self.client.model,
                        total_duration=verify_result.duration_seconds,
                        message=f"Successfully healed in {attempt_idx} attempt(s).",
                    )
                else:
                    self._notify(f"❌ Patch failed verification. Retrying with error feedback...")
                    last_error = f"{verify_result.stdout}\n{verify_result.stderr}"[-1000:]
                    attempts.append(HealAttempt(
                        attempt_number=attempt_idx,
                        failure=target_failure,
                        patch_diff=diff,
                        success=False,
                        error_message=last_error,
                    ))

            except Exception as e:
                self._notify(f"⚠️ Error during attempt {attempt_idx}: {str(e)}")
                last_error = str(e)

        # If we exhausted attempts, safely rollback
        self._notify("🛡️ Max attempts exceeded. Rolling back working tree to original state.")
        self.git.rollback()

        return HealResult(
            initial_passed=False,
            healed=False,
            attempts=attempts,
            final_diff="",
            model_used=self.client.model,
            total_duration=0.0,
            message=f"Failed to heal after {self.max_attempts} attempts. Workspace safely restored.",
        )
