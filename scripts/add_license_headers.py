#!/usr/bin/env python3
"""
Utility script to add license headers to Python files.

Usage:
    python scripts/add_license_headers.py
"""

import os
from pathlib import Path

LICENSE_HEADER = '''"""
Copyright (c) 2024 GUARDIAN Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

'''


def should_add_header(filepath: Path) -> bool:
    """Check if file should have a license header."""
    # Skip test files and generated files
    if "test" in str(filepath).lower() or "__pycache__" in str(filepath):
        return False
    
    # Skip __init__.py files
    if filepath.name == "__init__.py":
        return False
        
    return True


def has_license_header(content: str) -> bool:
    """Check if content already has a license header."""
    return "Copyright" in content[:500] or "MIT License" in content[:500]


def add_header_to_file(filepath: Path, dry_run: bool = True):
    """Add license header to a Python file."""
    if not should_add_header(filepath):
        return
    
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return
    
    if has_license_header(content):
        print(f"✓ {filepath} - Already has header")
        return
    
    # Check if file has shebang
    lines = content.split("\n")
    shebang = ""
    start_index = 0
    
    if lines and lines[0].startswith("#!"):
        shebang = lines[0] + "\n"
        start_index = 1
    
    # Check if file has docstring
    docstring_start = -1
    docstring_end = -1
    in_docstring = False
    
    for i, line in enumerate(lines[start_index:], start=start_index):
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_docstring:
                docstring_start = i
                in_docstring = True
                if stripped.endswith('"""') or stripped.endswith("'''"):
                    docstring_end = i
                    break
            else:
                docstring_end = i
                break
    
    # Add header after shebang and docstring
    if docstring_end > -1:
        insert_index = docstring_end + 1
        new_content = (
            shebang +
            "\n".join(lines[start_index:insert_index]) + "\n\n" +
            LICENSE_HEADER.strip() + "\n\n" +
            "\n".join(lines[insert_index:])
        )
    else:
        new_content = shebang + LICENSE_HEADER + "\n".join(lines[start_index:])
    
    if dry_run:
        print(f"Would add header to: {filepath}")
    else:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"✓ Added header to: {filepath}")


def main():
    """Main function."""
    root = Path(__file__).parent.parent
    
    # Find all Python files
    python_files = []
    for pattern in ["agents/**/*.py", "GUARDIAN/**/*.py", "app/**/*.py", "scripts/*.py"]:
        python_files.extend(root.glob(pattern))
    
    print(f"Found {len(python_files)} Python files")
    print("\nDry run (no changes will be made):")
    print("-" * 60)
    
    for filepath in python_files:
        add_header_to_file(filepath, dry_run=True)
    
    print("\n" + "=" * 60)
    response = input("\nAdd license headers to these files? [y/N]: ")
    
    if response.lower() == "y":
        print("\nAdding headers...")
        for filepath in python_files:
            add_header_to_file(filepath, dry_run=False)
        print("\n✓ Done!")
    else:
        print("\nCancelled.")


if __name__ == "__main__":
    main()
