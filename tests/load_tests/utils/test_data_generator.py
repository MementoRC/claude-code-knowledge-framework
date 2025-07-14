"""
Test data generation utilities for UCKN load testing.
"""

import random
import string

TECH_STACKS = [
    ["python", "pytest"],
    ["javascript", "nodejs"],
    ["java", "spring"],
    ["go", "gin"],
    ["csharp", ".net"],
    ["ruby", "rails"],
    ["typescript", "nestjs"],
]

PATTERN_TYPES = [
    "singleton",
    "factory",
    "observer",
    "strategy",
    "test",
    "integration",
    "api",
    "cli",
]


def random_string(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_pattern(complexity=None):
    """Generate a realistic pattern for addition."""
    tech_stack = random.choice(TECH_STACKS)
    pattern_type = random.choice(PATTERN_TYPES)
    complexity = complexity or random.choice(["low", "medium", "high"])
    content = f"# {pattern_type.title()} Pattern Example\n"
    if "python" in tech_stack:
        content += (
            f"class {pattern_type.title()}:\n    def __init__(self):\n        pass\n"
        )
    elif "javascript" in tech_stack:
        content += f"function {pattern_type}() {{}}\n"
    else:
        content += f"// {pattern_type} pattern in {tech_stack[0]}\n"
    return {
        "id": random_string(16),
        "title": f"{pattern_type.title()} Pattern ({random_string(4)})",
        "description": f"Auto-generated {pattern_type} pattern for load testing.",
        "content": content,
        "language": tech_stack[0],
        "tags": [pattern_type, tech_stack[0]],
        "metadata": {
            "complexity": complexity,
            "size": random.choice(["small", "medium", "large"]),
            "technology_stack": ",".join(tech_stack),
            "pattern_type": pattern_type,
            "success_rate": round(random.uniform(0.5, 1.0), 2),
            "pattern_id": random_string(12),
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
    }


def generate_search_queries(n=100):
    """Generate a list of realistic search queries."""
    queries = []
    for _ in range(n):
        tech = random.choice(TECH_STACKS)
        pattern = random.choice(PATTERN_TYPES)
        queries.append(f"{pattern} {tech[0]}")
    return queries
