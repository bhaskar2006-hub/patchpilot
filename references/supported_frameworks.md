# Supported Testing Frameworks & Adapters

PatchPilot natively parses and repairs test failures across major programming languages and testing frameworks.

| Language | Framework | Autodetect File | Output Format Handled |
| :--- | :--- | :--- | :--- |
| **Python** | `pytest` | `pytest.ini`, `pyproject.toml`, `tests/` | Standard Pytest failure blocks & short summary |
| **Python** | `unittest` | `test_*.py` | Standard Python traceback |
| **JS / TS** | `jest` | `package.json`, `jest.config.js` | Jest `● <testName>` failure blocks |
| **JS / TS** | `vitest` | `vitest.config.ts`, `package.json` | Vitest stack trace logs |
| **Rust** | `cargo test` | `Cargo.toml` | Rust panics and assertion fails |
| **Go** | `go test` | `go.mod` | `--- FAIL: <TestName>` blocks |
