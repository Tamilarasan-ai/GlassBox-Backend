"""Calculator Tool - Safe Math Evaluation"""
import ast
import operator
from typing import Any

from app.core.exceptions import ToolExecutionError


class Calculator:
    """
    Safe calculator tool for mathematical expressions
    
    Only allows basic arithmetic operations to prevent code injection.
    Returns string results or error messages to allow agent self-correction.
    """
    
    # Allowed operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    def execute(self, expression: str) -> str:
        """
        Safely evaluate a mathematical expression
        
        Args:
            expression: Math expression string (e.g., "2 + 3 * 4")
            
        Returns:
            Result of the calculation as a string, or an error message
        """
        try:
            # Parse expression
            # mode='eval' ensures it's a single expression, not statements
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate safely
            result = self._eval_node(tree.body)
            
            # Format result (avoid .0 for integers if possible, but float is fine)
            return str(result)
            
        except ZeroDivisionError:
            return "Error: Cannot divide by zero"
        except (SyntaxError, ValueError, KeyError, TypeError) as e:
            return f"Error: Invalid expression ({str(e)})"
        except Exception as e:
            return f"Error: Calculation failed ({str(e)})"
    
    def _eval_node(self, node: Any) -> float:
        """
        Recursively evaluate AST nodes
        
        Args:
            node: AST node to evaluate
            
        Returns:
            Evaluated result
        """
        if isinstance(node, ast.Constant):  # Python 3.8+ (includes numbers)
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Constants must be numbers")
            
        elif isinstance(node, ast.Num):  # Deprecated in 3.8 but good for compat
            return node.n
            
        elif isinstance(node, ast.BinOp):  # Binary operation
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return op(left, right)
            
        elif isinstance(node, ast.UnaryOp):  # Unary operation
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            operand = self._eval_node(node.operand)
            return op(operand)
            
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    @property
    def description(self) -> str:
        """Tool description for prompt building"""
        return "Performs basic arithmetic calculations (+, -, *, /, **). Returns string result or error message."
    
    @property
    def parameters(self) -> dict:
        """Expected parameters"""
        return {
            "expression": "Mathematical expression string (e.g., '2 + 3 * 4')"
        }
