def add(a: int, b: int) -> int:
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b

def multiply(a: int, b: int) -> int:
    return a * b

def divide(a: int, b: int) -> float:
    # Deliberate bug for demo: returns 0 on zero instead of raising ValueError as expected by test
    if b == 0:
        return 0.0
    return a / b
