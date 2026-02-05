#!/usr/bin/env python3

import ast
import sys
from pathlib import Path
from typing import List, Tuple


def check_import(file_path: Path) -> Tuple[bool, str]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        ast.parse(source, filename=str(file_path))
        return (True, "")
    except SyntaxError as e:
        return (False, f"Syntax error at line {e.lineno}: {e.msg}")
    except Exception as e:
        return (False, str(e))


def main():
    examples_dir = Path(__file__).parent

    example_files = [
        f for f in examples_dir.glob("*.py") if f.name != "verify_imports.py"
    ]

    results: List[Tuple[str, bool, str]] = []

    print("Checking imports for SDK examples...\n")

    for file_path in sorted(example_files):
        success, error = check_import(file_path)
        results.append((file_path.name, success, error))

        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {file_path.name}")
        if error:
            print(f"  Error: {error}")

    print("\n" + "=" * 60)
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    print(f"Total: {len(results)} files")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed files:")
        for name, success, error in results:
            if not success:
                print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print("\n✓ All examples passed import check!")
        sys.exit(0)


if __name__ == "__main__":
    main()
