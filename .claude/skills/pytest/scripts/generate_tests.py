#!/usr/bin/env python3
"""
Test file generator for Python projects.

Analyzes Python source files and generates corresponding pytest test files
with proper structure, fixtures, and common test patterns.
"""

import ast
import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional


class FunctionInfo:
    """Information about a function to be tested."""
    def __init__(self, name: str, is_async: bool, args: List[str], has_return: bool):
        self.name = name
        self.is_async = is_async
        self.args = args
        self.has_return = has_return


class ClassInfo:
    """Information about a class to be tested."""
    def __init__(self, name: str, methods: List[FunctionInfo]):
        self.name = name
        self.methods = methods


class CodeAnalyzer(ast.NodeVisitor):
    """Analyzes Python source code to extract testable components."""

    def __init__(self):
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.imports: List[str] = []
        self.is_fastapi = False

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
            if 'fastapi' in alias.name.lower():
                self.is_fastapi = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
            if 'fastapi' in node.module.lower():
                self.is_fastapi = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if not node.name.startswith('_'):
            args = [arg.arg for arg in node.args.args if arg.arg != 'self']
            has_return = any(isinstance(n, ast.Return) and n.value for n in ast.walk(node))
            func_info = FunctionInfo(node.name, False, args, has_return)
            self.functions.append(func_info)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if not node.name.startswith('_'):
            args = [arg.arg for arg in node.args.args if arg.arg != 'self']
            has_return = any(isinstance(n, ast.Return) and n.value for n in ast.walk(node))
            func_info = FunctionInfo(node.name, True, args, has_return)
            self.functions.append(func_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if not node.name.startswith('_'):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith('_') or item.name == '__init__':
                        args = [arg.arg for arg in item.args.args if arg.arg != 'self']
                        has_return = any(isinstance(n, ast.Return) and n.value for n in ast.walk(item))
                        is_async = isinstance(item, ast.AsyncFunctionDef)
                        methods.append(FunctionInfo(item.name, is_async, args, has_return))

            if methods:
                self.classes.append(ClassInfo(node.name, methods))
        self.generic_visit(node)


class TestGenerator:
    """Generates pytest test files from analyzed code."""

    def __init__(self, source_file: Path, test_file: Path, analyzer: CodeAnalyzer):
        self.source_file = source_file
        self.test_file = test_file
        self.analyzer = analyzer

    def generate(self) -> str:
        """Generate complete test file content."""
        parts = []

        # Header
        parts.append(self._generate_header())

        # Imports
        parts.append(self._generate_imports())

        # Fixtures
        if self.analyzer.classes or self.analyzer.is_fastapi:
            parts.append(self._generate_fixtures())

        # Function tests
        for func in self.analyzer.functions:
            parts.append(self._generate_function_test(func))

        # Class tests
        for cls in self.analyzer.classes:
            parts.append(self._generate_class_tests(cls))

        return '\n\n'.join(parts) + '\n'

    def _generate_header(self) -> str:
        module_path = self.source_file.stem
        return f'''"""
Tests for {module_path}.

This test file was auto-generated and should be customized for your specific use case.
"""'''

    def _generate_imports(self) -> str:
        imports = ['import pytest']

        # Add asyncio import if needed
        if any(f.is_async for f in self.analyzer.functions):
            imports.append('import pytest')
            imports.append('from unittest.mock import AsyncMock, MagicMock, patch')
        else:
            imports.append('from unittest.mock import MagicMock, patch')

        # Add FastAPI imports if needed
        if self.analyzer.is_fastapi:
            imports.extend([
                'from fastapi.testclient import TestClient',
                'from httpx import AsyncClient'
            ])

        # Add import for the module being tested
        module_name = self.source_file.stem
        parent_module = self.source_file.parent.name
        if parent_module and parent_module != 'tests':
            imports.append(f'from {parent_module}.{module_name} import *')
        else:
            imports.append(f'from {module_name} import *')

        return '\n'.join(imports)

    def _generate_fixtures(self) -> str:
        fixtures = []

        # FastAPI fixtures
        if self.analyzer.is_fastapi:
            fixtures.append('''@pytest.fixture
def client():
    """TestClient fixture for FastAPI testing."""
    from main import app  # Adjust import based on your app location
    return TestClient(app)


@pytest.fixture
async def async_client():
    """AsyncClient fixture for async FastAPI testing."""
    from main import app  # Adjust import based on your app location
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac''')

        # Class fixtures
        for cls in self.analyzer.classes:
            fixture_name = cls.name.lower()
            fixtures.append(f'''@pytest.fixture
def {fixture_name}():
    """Fixture for {cls.name} instance."""
    return {cls.name}()''')

        return '\n\n\n'.join(fixtures)

    def _generate_function_test(self, func: FunctionInfo) -> str:
        """Generate test for a standalone function."""
        test_name = f'test_{func.name}'
        decorator = '@pytest.mark.asyncio\n' if func.is_async else ''
        async_keyword = 'async ' if func.is_async else ''
        await_keyword = 'await ' if func.is_async else ''

        # Generate parameter setup
        params_setup = []
        for arg in func.args:
            params_setup.append(f'    {arg} = None  # TODO: Provide test value')
        params_str = ', '.join(func.args) if func.args else ''

        # Generate test body
        if func.has_return:
            test_body = f'''    # Arrange
{chr(10).join(params_setup) if params_setup else "    pass"}

    # Act
    result = {await_keyword}{func.name}({params_str})

    # Assert
    assert result is not None  # TODO: Add specific assertions'''
        else:
            test_body = f'''    # Arrange
{chr(10).join(params_setup) if params_setup else "    pass"}

    # Act
    {await_keyword}{func.name}({params_str})

    # Assert
    # TODO: Add assertions to verify side effects'''

        return f'''{decorator}def {async_keyword}{test_name}():
    """Test {func.name} function."""
{test_body}'''

    def _generate_class_tests(self, cls: ClassInfo) -> str:
        """Generate tests for a class."""
        tests = []
        fixture_name = cls.name.lower()

        for method in cls.methods:
            if method.name == '__init__':
                # Test initialization
                tests.append(f'''def test_{cls.name.lower()}_initialization({fixture_name}):
    """Test {cls.name} initialization."""
    assert {fixture_name} is not None
    # TODO: Add assertions for initialized state''')
            else:
                test_name = f'test_{cls.name.lower()}_{method.name}'
                decorator = '@pytest.mark.asyncio\n' if method.is_async else ''
                async_keyword = 'async ' if method.is_async else ''
                await_keyword = 'await ' if method.is_async else ''

                # Generate parameter setup
                params_setup = []
                for arg in method.args:
                    params_setup.append(f'    {arg} = None  # TODO: Provide test value')
                params_str = ', '.join(method.args) if method.args else ''

                if method.has_return:
                    test_body = f'''    # Arrange
{chr(10).join(params_setup) if params_setup else "    pass"}

    # Act
    result = {await_keyword}{fixture_name}.{method.name}({params_str})

    # Assert
    assert result is not None  # TODO: Add specific assertions'''
                else:
                    test_body = f'''    # Arrange
{chr(10).join(params_setup) if params_setup else "    pass"}

    # Act
    {await_keyword}{fixture_name}.{method.name}({params_str})

    # Assert
    # TODO: Add assertions to verify side effects'''

                tests.append(f'''{decorator}def {async_keyword}{test_name}({fixture_name}):
    """Test {cls.name}.{method.name} method."""
{test_body}''')

        return '\n\n\n'.join(tests)


def analyze_file(file_path: Path) -> CodeAnalyzer:
    """Analyze a Python source file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    return analyzer


def generate_test_file(source_file: Path, output_dir: Optional[Path] = None, force: bool = False) -> Path:
    """Generate a test file for the given source file."""
    # Determine output path
    if output_dir:
        test_file = output_dir / f'test_{source_file.name}'
    else:
        # Place in tests/ directory parallel to source
        if source_file.parent.name == 'app' or source_file.parent.name == 'src':
            tests_dir = source_file.parent.parent / 'tests'
        else:
            tests_dir = source_file.parent / 'tests'

        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / f'test_{source_file.name}'

    # Check if test file already exists
    if test_file.exists() and not force:
        print(f"Test file already exists: {test_file}")
        print("Use --force to overwrite")
        return test_file

    # Analyze source file
    analyzer = analyze_file(source_file)

    # Generate test content
    generator = TestGenerator(source_file, test_file, analyzer)
    test_content = generator.generate()

    # Write test file
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    print(f"Generated test file: {test_file}")
    return test_file


def main():
    parser = argparse.ArgumentParser(
        description='Generate pytest test files from Python source code'
    )
    parser.add_argument(
        'source_file',
        type=Path,
        help='Python source file to generate tests for'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output directory for test file (default: tests/ directory)'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Overwrite existing test file'
    )

    args = parser.parse_args()

    if not args.source_file.exists():
        print(f"Error: Source file not found: {args.source_file}", file=sys.stderr)
        sys.exit(1)

    if not args.source_file.suffix == '.py':
        print(f"Error: Source file must be a Python file (.py)", file=sys.stderr)
        sys.exit(1)

    generate_test_file(args.source_file, args.output, args.force)


if __name__ == '__main__':
    main()
