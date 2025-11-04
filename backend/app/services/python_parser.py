"""
Python parser for analog layout modules

Extracts class and function definitions from Python files used for
programmatic analog layout generation.
"""
import ast
import logging
from typing import List, Dict, Any

from app.schemas.module import PythonMethod, PythonModuleMetadata

logger = logging.getLogger(__name__)


class PythonParser:
    """Parser for Python files containing analog layout code"""

    def parse_file(self, file_content: str, filename: str = "layout.py") -> List[Dict[str, Any]]:
        """
        Parse a Python file and extract class/function information

        Args:
            file_content: Python file content
            filename: Original filename

        Returns:
            List of module dictionaries (classes and functions)
        """
        try:
            # Parse Python code to AST
            tree = ast.parse(file_content, filename=filename)

            modules = []

            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._parse_class(node, file_content)
                    if class_info:
                        modules.append(class_info)

                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions (not methods)
                    if self._is_top_level(node, tree):
                        func_info = self._parse_function(node, file_content)
                        if func_info:
                            modules.append(func_info)

            return modules

        except SyntaxError as e:
            logger.error(f"Syntax error in Python file: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing Python file: {e}")
            return []

    def _is_top_level(self, node: ast.AST, tree: ast.Module) -> bool:
        """Check if a node is at module level (not nested)"""
        for item in tree.body:
            if item == node:
                return True
        return False

    def _parse_class(self, node: ast.ClassDef, source: str) -> Dict[str, Any]:
        """
        Parse a class definition

        Args:
            node: AST ClassDef node
            source: Original source code

        Returns:
            Class information dictionary
        """
        # Get docstring
        docstring = ast.get_docstring(node)

        # Get base classes
        base_classes = [self._get_name(base) for base in node.bases]

        # Get methods
        methods = []
        attributes = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = {
                    "name": item.name,
                    "is_static": any(isinstance(d, ast.Name) and d.id == 'staticmethod' for d in item.decorator_list),
                    "is_classmethod": any(isinstance(d, ast.Name) and d.id == 'classmethod' for d in item.decorator_list),
                    "docstring": ast.get_docstring(item),
                    "parameters": [arg.arg for arg in item.args.args]
                }
                methods.append(method_info)

            elif isinstance(item, ast.Assign):
                # Class-level attributes
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        # Get line numbers
        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line

        return {
            "name": node.name,
            "module_type": "python_class",
            "start_line": start_line,
            "end_line": end_line,
            "description": docstring or f"Python class {node.name}",
            "metadata": {
                "methods": methods,
                "attributes": attributes,
                "base_classes": base_classes,
                "docstring": docstring
            }
        }

    def _parse_function(self, node: ast.FunctionDef, source: str) -> Dict[str, Any]:
        """
        Parse a function definition

        Args:
            node: AST FunctionDef node
            source: Original source code

        Returns:
            Function information dictionary
        """
        # Get docstring
        docstring = ast.get_docstring(node)

        # Get parameters
        parameters = [arg.arg for arg in node.args.args]

        # Get line numbers
        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line

        # Check if it's a generator
        is_generator = any(isinstance(n, ast.Yield) for n in ast.walk(node))

        return {
            "name": node.name,
            "module_type": "python_function",
            "start_line": start_line,
            "end_line": end_line,
            "description": docstring or f"Python function {node.name}",
            "metadata": {
                "parameters": parameters,
                "docstring": docstring,
                "is_generator": is_generator,
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
            }
        }

    def _get_name(self, node: ast.AST) -> str:
        """Get the name from an AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return "Unknown"

    def _get_decorator_name(self, node: ast.AST) -> str:
        """Get decorator name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        else:
            return "unknown_decorator"


# Global parser instance
python_parser = PythonParser()
