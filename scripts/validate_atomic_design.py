#!/usr/bin/env python3
"""
Validate Atomic Design principles in UCKN architecture.
Ensures proper layering and no circular dependencies.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class AtomicDesignValidator:
    """Validates atomic design principles in the codebase."""
    
    def __init__(self, src_path: str = "src/uckn"):
        self.src_path = Path(src_path)
        self.violations: List[str] = []
        
        # Define layer hierarchy (lower can't import higher)
        self.layer_hierarchy = {
            "atoms": 0,
            "molecules": 1,
            "organisms": 2,
            "bridge": 3,
            "api": 4,
        }
        
    def get_layer(self, file_path: Path) -> str:
        """Determine which atomic layer a file belongs to."""
        parts = file_path.parts
        for part in parts:
            if part in self.layer_hierarchy:
                return part
        return "other"
    
    def extract_imports(self, file_path: Path) -> Set[str]:
        """Extract all imports from a Python file."""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
        except Exception as e:
            self.violations.append(f"Error parsing {file_path}: {e}")
            
        return imports
    
    def check_layer_violations(self, file_path: Path, imports: Set[str]) -> None:
        """Check if imports violate layer hierarchy."""
        file_layer = self.get_layer(file_path)
        if file_layer not in self.layer_hierarchy:
            return
            
        file_level = self.layer_hierarchy[file_layer]
        
        for imp in imports:
            if not imp.startswith("uckn."):
                continue
                
            # Extract layer from import
            parts = imp.split(".")
            for i, part in enumerate(parts):
                if part in self.layer_hierarchy:
                    import_level = self.layer_hierarchy[part]
                    
                    # Check if importing from higher layer
                    if import_level > file_level:
                        self.violations.append(
                            f"Layer violation: {file_path} ({file_layer}) imports "
                            f"from {imp} ({part})"
                        )
                    break
    
    def check_file_sizes(self) -> None:
        """Check that files are within size constraints."""
        for root, dirs, files in os.walk(self.src_path):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            
            for file in files:
                if not file.endswith(".py") or file == "__init__.py":
                    continue
                    
                file_path = Path(root) / file
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                        
                    if line_count > 500:
                        self.violations.append(
                            f"File size violation: {file_path} has {line_count} lines "
                            f"(exceeds 500)"
                        )
                except Exception as e:
                    self.violations.append(f"Error reading {file_path}: {e}")
    
    def check_cross_layer_imports(self) -> None:
        """Check for improper imports between layers."""
        for root, dirs, files in os.walk(self.src_path):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            
            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                file_path = Path(root) / file
                imports = self.extract_imports(file_path)
                self.check_layer_violations(file_path, imports)
    
    def validate(self) -> bool:
        """Run all validations."""
        print("🏗️ Validating Atomic Design principles...")
        
        # Check directory structure
        required_dirs = [
            self.src_path / "core" / "atoms",
            self.src_path / "core" / "molecules",
            self.src_path / "core" / "organisms",
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                self.violations.append(f"Missing required directory: {dir_path}")
        
        # Check file sizes
        self.check_file_sizes()
        
        # Check cross-layer imports
        self.check_cross_layer_imports()
        
        # Report results
        if self.violations:
            print("❌ Atomic Design violations found:")
            for violation in self.violations:
                print(f"  - {violation}")
            return False
        else:
            print("✅ All Atomic Design principles validated!")
            return True


def main():
    """Run the validator."""
    validator = AtomicDesignValidator()
    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()