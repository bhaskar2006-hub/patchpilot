import pytest
from patchpilot.parser import TestLogParser

PYTEST_SAMPLE_OUTPUT = """
============================= test session starts ==============================
collected 2 items

tests/test_math.py .F                                                    [100%]

=================================== FAILURES ===================================
_________________________________ test_divide __________________________________

    def test_divide():
>       assert divide(10, 0) == 0
E       ZeroDivisionError: division by zero

tests/test_math.py:14: ZeroDivisionError
=========================== short test summary info ============================
FAILED tests/test_math.py::test_divide - ZeroDivisionError: division by zero
========================= 1 failed, 1 passed in 0.05s ==========================
"""

JEST_SAMPLE_OUTPUT = """
FAIL src/calculator.test.ts
  ● Calculator › divides by zero

    expect(received).toThrow()

      12 | test('divides by zero', () => {
    > 13 |   expect(() => divide(10, 0)).toThrow('Cannot divide by zero');
         |                                ^
      14 | });

      at Object.<anonymous> (src/calculator.test.ts:13:32)
"""

def test_detect_framework():
    assert TestLogParser.detect_framework(PYTEST_SAMPLE_OUTPUT) == "pytest"
    assert TestLogParser.detect_framework(JEST_SAMPLE_OUTPUT) == "jest"

def test_parse_pytest():
    failures = TestLogParser.parse(PYTEST_SAMPLE_OUTPUT)
    assert len(failures) == 1
    assert failures[0].test_name == "test_divide"
    assert "test_math.py" in failures[0].file_path
    assert failures[0].line_number == 14
    assert "ZeroDivisionError" in failures[0].error_message

def test_parse_jest():
    failures = TestLogParser.parse(JEST_SAMPLE_OUTPUT)
    assert len(failures) == 1
    assert "calculator.test.ts" in failures[0].file_path
    assert failures[0].line_number == 13
