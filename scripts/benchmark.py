"""Benchmark script to test PatchPilot against synthetic bugs."""

import sys
import os
import tempfile
import time
from patchpilot.engine import SelfHealingEngine


BENCHMARK_CASES = [
    {
        "name": "Off-by-one Error",
        "file_name": "calc.py",
        "broken_code": """def calculate_total(items):\n    # Bug: ignores first item\n    return sum(items[1:])\n""",
        "test_code": """from calc import calculate_total\n\ndef test_total():\n    assert calculate_total([10, 20, 30]) == 60\n""",
    },
    {
        "name": "Division by Zero Handing",
        "file_name": "math_ops.py",
        "broken_code": """def safe_divide(a, b):\n    return a / b\n""",
        "test_code": """from math_ops import safe_divide\n\ndef test_zero():\n    assert safe_divide(10, 0) == 0\n    assert safe_divide(10, 2) == 5\n""",
    },
]


def run_benchmark():
    print("=" * 60)
    print("🚀 Running PatchPilot Benchmark Suite on Local Open-Weight SLMs")
    print("=" * 60)

    passed_count = 0
    start_all = time.time()

    for idx, case in enumerate(BENCHMARK_CASES, 1):
        print(f"\n[Case {idx}/{len(BENCHMARK_CASES)}] {case['name']}")
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write broken code and test
            with open(os.path.join(temp_dir, case["file_name"]), "w") as f:
                f.write(case["broken_code"])
            with open(os.path.join(temp_dir, "test_benchmark.py"), "w") as f:
                f.write(case["test_code"])

            engine = SelfHealingEngine(workspace_dir=temp_dir, max_attempts=2)
            result = engine.heal("pytest test_benchmark.py")

            if result.healed:
                print(f"  ✅ HEALED in {len(result.attempts)} attempt(s)")
                passed_count += 1
            else:
                print(f"  ❌ Failed to heal: {result.message}")

    total_time = time.time() - start_all
    print("\n" + "=" * 60)
    print(f"Benchmark Results: {passed_count}/{len(BENCHMARK_CASES)} resolved ({passed_count/len(BENCHMARK_CASES)*100:.1f}%) in {total_time:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
