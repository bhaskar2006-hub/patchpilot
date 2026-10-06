from patchpilot.runner import TestRunner

def test_run_command_success():
    res = TestRunner.run("echo 'Hello World'")
    assert res.passed is True
    assert res.exit_code == 0
    assert "Hello World" in res.stdout

def test_run_command_failure():
    res = TestRunner.run("python3 -c 'raise ValueError(\"Error\")'")
    assert res.passed is False
    assert res.exit_code != 0
    assert "ValueError: Error" in res.stderr
