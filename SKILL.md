---
name: patchpilot
description: Autonomous self-healing CI/CD & test repair engine powered by local open-weight SLMs (Qwen 2.5 Coder, Gemma 2, Llama 3). Use when unit or integration tests fail, CI pipelines break, or when automated code debugging and surgical test repair are requested.
---

# PatchPilot: Self-Healing CI/CD Agent Skill

PatchPilot is an autonomous code repair engine that detects test suite failures, isolates the root causes, and prompts local open-weight SLMs to synthesize surgical fixes that are verified in a sandboxed test loop before being committed.

## When to Use This Skill
Activate this skill when:
- Unit, integration, or E2E tests fail (Pytest, Jest/Vitest, Cargo, Go, Unittest).
- You are asked to "fix the failing tests", "auto-heal CI", or "debug test errors".
- You want zero external API dependency by leveraging local open-weight models (Ollama, vLLM, llama.cpp).
- You want surgical patches validated deterministically before committing.

## Quick Start & CLI Workflows

### 1. Autonomous Healing (Recommended)
Run the self-healing loop in the current workspace:
```bash
# Auto-detects test runner (pytest, npm test, cargo test, go test)
patchpilot heal

# Or target a specific test command and model
patchpilot heal --cmd "pytest tests/test_core.py" --model "qwen2.5-coder:1.5b" --commit
```

### 2. Failure Diagnostics Only
To inspect failing assertions, stack traces, and culprit files without modifying code:
```bash
patchpilot diagnose
```

### 3. Check Local Open-Weight Models
List installed local SLMs ready for code synthesis:
```bash
patchpilot models
```

---

## Agent Operational Instructions

When an agent is operating in an environment with failing tests:

1. **Step 1: Check Environment Health**
   Verify local SLM availability:
   ```bash
   patchpilot models
   ```

2. **Step 2: Diagnose Failures**
   Run diagnosis to isolate broken files and line numbers:
   ```bash
   patchpilot diagnose --cmd "<test-command>"
   ```

3. **Step 3: Trigger Self-Repair Loop**
   Execute the automated loop with verification:
   ```bash
   patchpilot heal --cmd "<test-command>" --max-attempts 3
   ```

4. **Step 4: Review Unified Diff**
   Inspect the surgical patch generated in git:
   ```bash
   git diff
   ```

## Supported Frameworks & Models

### Testing Frameworks:
- **Python**: `pytest`, `unittest`
- **JavaScript / TypeScript**: `jest`, `vitest`, `npm test`
- **Rust**: `cargo test`
- **Go**: `go test ./...`

### Local Open-Weight Models:
- `qwen2.5-coder:1.5b` / `qwen2.5-coder:7b` *(Top Recommended for code repair)*
- `gemma2:2b` / `gemma2:9b`
- `deepseek-coder:6.7b`
- `llama3.2:3b`
