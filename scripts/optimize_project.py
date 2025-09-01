#!/usr/bin/env python3
"""
Project optimization script for Carbon-Aware FinOps.
Performs various cleanup and optimization tasks.
"""

import os
import sys
import subprocess
import ast
from pathlib import Path
from typing import Set, List, Dict

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.logging_config import get_logger

logger = get_logger('project-optimizer')


class ProjectOptimizer:
    """Performs various project optimization tasks."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / 'src'
        
    def find_unused_imports(self) -> Dict[str, List[str]]:
        """Find unused imports in Python files."""
        unused_imports = {}
        
        for py_file in self.src_dir.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
                
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                
                imports = set()
                used_names = set()
                
                # Collect imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports.add(alias.name)
                
                # Collect used names
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                        used_names.add(node.id)
                    elif isinstance(node, ast.Attribute):
                        if isinstance(node.value, ast.Name):
                            used_names.add(node.value.id)
                
                # Find unused imports
                unused = imports - used_names
                if unused:
                    unused_imports[str(py_file)] = list(unused)
                    
            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")
        
        return unused_imports
    
    def check_code_quality(self) -> Dict[str, int]:
        """Check code quality metrics."""
        results = {}
        
        try:
            # Run flake8
            result = subprocess.run(
                ['flake8', str(self.src_dir), '--count', '--statistics'],
                capture_output=True, text=True
            )
            results['flake8_errors'] = result.returncode
            
            # Run mypy
            result = subprocess.run(
                ['mypy', str(self.src_dir), '--ignore-missing-imports'],
                capture_output=True, text=True
            )
            results['mypy_errors'] = result.returncode
            
        except FileNotFoundError:
            logger.warning("Code quality tools not installed")
        
        return results
    
    def find_large_files(self, size_mb: float = 1.0) -> List[Path]:
        """Find files larger than specified size."""
        large_files = []
        size_bytes = size_mb * 1024 * 1024
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size > size_bytes:
                # Skip venv and .git directories
                if 'venv' not in str(file_path) and '.git' not in str(file_path):
                    large_files.append(file_path)
        
        return sorted(large_files, key=lambda x: x.stat().st_size, reverse=True)
    
    def find_duplicate_code(self) -> List[str]:
        """Find potential duplicate code patterns."""
        duplicates = []
        
        # Simple heuristic: look for functions with similar names
        function_patterns = {}
        
        for py_file in self.src_dir.rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        pattern = node.name.lower().replace('_', '')
                        if pattern in function_patterns:
                            function_patterns[pattern].append(str(py_file))
                        else:
                            function_patterns[pattern] = [str(py_file)]
            
            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")
        
        # Find patterns with multiple files
        for pattern, files in function_patterns.items():
            if len(files) > 1:
                duplicates.append(f"Similar functions '{pattern}' in: {', '.join(files)}")
        
        return duplicates
    
    def check_dependencies(self) -> Dict[str, List[str]]:
        """Check for dependency issues."""
        issues = {}
        
        requirements_files = [
            self.project_root / 'requirements.txt',
            self.project_root / 'requirements-dev.txt'
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                with open(req_file, 'r') as f:
                    lines = f.readlines()
                
                file_issues = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Check for version pinning
                        if '==' not in line and '>=' not in line and '~=' not in line:
                            file_issues.append(f"No version specified: {line}")
                        
                        # Check for very old versions
                        if any(old in line.lower() for old in ['==1.', '==2.0', '==0.']):
                            file_issues.append(f"Potentially outdated: {line}")
                
                if file_issues:
                    issues[str(req_file)] = file_issues
        
        return issues
    
    def optimize_project(self) -> Dict[str, any]:
        """Run all optimization checks."""
        logger.info("Starting project optimization analysis...")
        
        results = {
            'unused_imports': self.find_unused_imports(),
            'code_quality': self.check_code_quality(),
            'large_files': [str(f) for f in self.find_large_files()],
            'potential_duplicates': self.find_duplicate_code(),
            'dependency_issues': self.check_dependencies()
        }
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate optimization report."""
        report = []
        report.append("# Carbon-Aware FinOps Project Optimization Report\n")
        
        # Unused imports
        if results['unused_imports']:
            report.append("## 🔍 Unused Imports")
            for file_path, imports in results['unused_imports'].items():
                report.append(f"**{file_path}:**")
                for imp in imports:
                    report.append(f"  - {imp}")
                report.append("")
        
        # Large files
        if results['large_files']:
            report.append("## 📦 Large Files (>1MB)")
            for file_path in results['large_files'][:10]:  # Top 10
                size = Path(file_path).stat().st_size / (1024 * 1024)
                report.append(f"  - {file_path} ({size:.1f} MB)")
            report.append("")
        
        # Potential duplicates
        if results['potential_duplicates']:
            report.append("## 🔄 Potential Code Duplicates")
            for duplicate in results['potential_duplicates']:
                report.append(f"  - {duplicate}")
            report.append("")
        
        # Dependency issues
        if results['dependency_issues']:
            report.append("## 📋 Dependency Issues")
            for file_path, issues in results['dependency_issues'].items():
                report.append(f"**{file_path}:**")
                for issue in issues:
                    report.append(f"  - {issue}")
                report.append("")
        
        # Code quality
        report.append("## ✅ Code Quality")
        quality = results['code_quality']
        report.append(f"  - Flake8 status: {'✅ Pass' if quality.get('flake8_errors', 1) == 0 else '❌ Issues found'}")
        report.append(f"  - MyPy status: {'✅ Pass' if quality.get('mypy_errors', 1) == 0 else '❌ Issues found'}")
        report.append("")
        
        # Recommendations
        report.append("## 💡 Recommendations")
        report.append("1. **Remove unused imports** to reduce file size and improve clarity")
        report.append("2. **Review large files** for potential optimization opportunities")
        report.append("3. **Check for duplicate code** and consider refactoring")
        report.append("4. **Update dependency versions** for security and performance")
        report.append("5. **Run code quality tools** regularly as part of CI/CD")
        
        return "\n".join(report)


def main():
    """Main optimization script."""
    project_root = os.path.join(os.path.dirname(__file__), '..')
    
    optimizer = ProjectOptimizer(project_root)
    results = optimizer.optimize_project()
    
    # Generate report
    report = optimizer.generate_report(results)
    
    # Save report
    report_file = Path(project_root) / 'OPTIMIZATION_REPORT.md'
    with open(report_file, 'w') as f:
        f.write(report)
    
    logger.info(f"Optimization report saved to {report_file}")
    
    # Print summary
    print("\n🔍 Project Optimization Summary")
    print("=" * 40)
    print(f"📁 Unused imports found: {len(results['unused_imports'])}")
    print(f"📦 Large files found: {len(results['large_files'])}")
    print(f"🔄 Potential duplicates: {len(results['potential_duplicates'])}")
    print(f"📋 Dependency issues: {sum(len(issues) for issues in results['dependency_issues'].values())}")
    print(f"📄 Full report: {report_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())