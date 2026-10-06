import os
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TestFailure:
    test_name: str
    file_path: str
    line_number: Optional[int]
    error_message: str
    stack_trace: str
    framework: str
    context_code: Optional[str] = None


class TestLogParser:
    """Extracts structured failure data and relevant code files from test output."""

    @staticmethod
    def parse(output: str, framework: Optional[str] = None) -> List[TestFailure]:
        if not framework:
            framework = TestLogParser.detect_framework(output)

        if framework == "pytest":
            return TestLogParser._parse_pytest(output)
        elif framework in ("jest", "vitest"):
            return TestLogParser._parse_jest(output)
        elif framework == "cargo":
            return TestLogParser._parse_cargo(output)
        elif framework == "go":
            return TestLogParser._parse_go(output)
        else:
            return TestLogParser._parse_generic(output)

    @staticmethod
    def detect_framework(output: str) -> str:
        if "=== FAILURES ===" in output or "pytest" in output or "collected " in output:
            return "pytest"
        if "FAIL " in output or "jest" in output or "vitest" in output or "● " in output:
            return "jest"
        if "running " in output and "failures:" in output and ("src/" in output or "tests/" in output):
            return "cargo"
        if "--- FAIL:" in output or "FAIL\t" in output:
            return "go"
        return "generic"

    @staticmethod
    def _parse_pytest(output: str) -> List[TestFailure]:
        failures: List[TestFailure] = []
        
        # Match Pytest failure blocks: ____________________ test_name ____________________
        sections = re.split(r"_{3,}\s+([^\n_][^\n]+?[^\n_])\s+_{3,}", output)
        
        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                test_name = sections[i]
                trace = sections[i + 1]
                
                # Extract file path & line
                # e.g.: test_calc.py:4: ... calc.py:2: ZeroDivisionError
                all_matches = re.findall(r"([^\s:]+\.py):(\d+):", trace)
                if all_matches:
                    # Prefer the deepest non-test source file if available
                    source_matches = [
                        (f, int(l)) for f, l in all_matches 
                        if not os.path.basename(f).startswith("test_") 
                        and not os.path.basename(f).endswith("_test.py")
                        and "conftest.py" not in f
                    ]
                    if source_matches:
                        file_path, line_no = source_matches[-1]
                    else:
                        file_path, line_no = all_matches[-1][0], int(all_matches[-1][1])
                else:
                    file_match = re.search(r"([^\s:]+\.py)", trace)
                    file_path = file_match.group(1) if file_match else "unknown.py"
                    line_no = None

                # Extract error message
                err_match = re.search(r"(E\s+.*|AssertionError:.*|Exception:.*|TypeError:.*|ValueError:.*)", trace)
                error_msg = err_match.group(0).strip() if err_match else "Test failed"

                failures.append(
                    TestFailure(
                        test_name=test_name,
                        file_path=file_path,
                        line_number=line_no,
                        error_message=error_msg,
                        stack_trace=trace.strip(),
                        framework="pytest",
                    )
                )

        if not failures:
            # Fallback for short pytest output: FAILED tests/test_foo.py::test_bar - AssertionError
            failed_lines = re.findall(r"FAILED\s+([\w\-./\\]+\.py)::([^\s\-]+)(?:\s+-\s+(.*))?", output)
            for file_path, test_name, err in failed_lines:
                failures.append(
                    TestFailure(
                        test_name=test_name,
                        file_path=file_path,
                        line_number=None,
                        error_message=err if err else "Test failed",
                        stack_trace=output,
                        framework="pytest",
                    )
                )

        return failures

    @staticmethod
    def _parse_jest(output: str) -> List[TestFailure]:
        failures: List[TestFailure] = []
        blocks = output.split("● ")
        
        for block in blocks[1:]:
            lines = block.strip().split("\n")
            test_name = lines[0].strip()
            
            file_match = re.search(r"at\s+.*?\(([\w\-./\\]+\.(?:ts|tsx|js|jsx)):(\d+):(\d+)\)", block)
            if file_match:
                file_path = file_match.group(1)
                line_no = int(file_match.group(2))
            else:
                fallback = re.search(r"FAIL\s+([\w\-./\\]+\.(?:ts|tsx|js|jsx))", output)
                file_path = fallback.group(1) if fallback else "unknown.js"
                line_no = None

            failures.append(
                TestFailure(
                    test_name=test_name,
                    file_path=file_path,
                    line_number=line_no,
                    error_message=lines[1].strip() if len(lines) > 1 else "Jest Assertion Error",
                    stack_trace=block.strip(),
                    framework="jest",
                )
            )
        return failures

    @staticmethod
    def _parse_cargo(output: str) -> List[TestFailure]:
        failures: List[TestFailure] = []
        for match in re.finditer(r"----\s+([^\s]+)\s+stdout\s+----\n(.*?)(?=\nfailures:|\Z)", output, re.DOTALL):
            test_name = match.group(1)
            trace = match.group(2)
            
            loc_match = re.search(r"at\s+([\w\-./\\]+\.rs):(\d+)", trace)
            file_path = loc_match.group(1) if loc_match else "src/lib.rs"
            line_no = int(loc_match.group(2)) if loc_match else None

            failures.append(
                TestFailure(
                    test_name=test_name,
                    file_path=file_path,
                    line_number=line_no,
                    error_message="Rust panic in test",
                    stack_trace=trace.strip(),
                    framework="cargo",
                )
            )
        return failures

    @staticmethod
    def _parse_go(output: str) -> List[TestFailure]:
        failures: List[TestFailure] = []
        matches = re.finditer(r"--- FAIL:\s+([^\s]+)\s+\([^\)]+\)\n(.*?)(?=\n=== RUN|\n--- FAIL|\nFAIL|\Z)", output, re.DOTALL)
        for match in matches:
            test_name = match.group(1)
            trace = match.group(2)
            
            loc_match = re.search(r"([\w\-./\\]+\.go):(\d+):", trace)
            file_path = loc_match.group(1) if loc_match else "unknown.go"
            line_no = int(loc_match.group(2)) if loc_match else None

            failures.append(
                TestFailure(
                    test_name=test_name,
                    file_path=file_path,
                    line_number=line_no,
                    error_message="Go test failure",
                    stack_trace=trace.strip(),
                    framework="go",
                )
            )
        return failures

    @staticmethod
    def _parse_generic(output: str) -> List[TestFailure]:
        file_match = re.search(r"([\w\-./\\]+\.(?:py|ts|js|rs|go|java|cpp|c)):(\d+)", output)
        file_path = file_match.group(1) if file_match else "unknown"
        line_no = int(file_match.group(2)) if file_match else None
        
        return [
            TestFailure(
                test_name="generic_failure",
                file_path=file_path,
                line_number=line_no,
                error_message="Execution or test failure",
                stack_trace=output[-2000:],
                framework="generic",
            )
        ]
