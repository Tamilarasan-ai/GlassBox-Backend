"""Unit tests for Calculator Tool"""
import pytest
from app.engine.tools.calculator import Calculator

def test_calculator_valid_expressions():
    calc = Calculator()
    
    assert calc.execute("2 + 2") == "4"
    assert calc.execute("10 - 4") == "6"
    assert calc.execute("3 * 5") == "15"
    assert calc.execute("20 / 4") == "5.0"
    assert calc.execute("2 ** 3") == "8"
    assert calc.execute("(2 + 3) * 4") == "20"
    assert calc.execute("-5 + 10") == "5"

def test_calculator_division_by_zero():
    calc = Calculator()
    
    result = calc.execute("10 / 0")
    assert "Error: Cannot divide by zero" in result

def test_calculator_invalid_syntax():
    calc = Calculator()
    
    result = calc.execute("2 +")
    assert "Error: Invalid expression" in result
    
    result = calc.execute("invalid")
    assert "Error: Invalid expression" in result

def test_calculator_security():
    calc = Calculator()
    
    # Attempt to import os
    result = calc.execute("__import__('os').system('ls')")
    assert "Error" in result
    assert "Unsupported expression" in result or "Invalid expression" in result
    
    # Attempt to access builtins
    result = calc.execute("print('hello')")
    assert "Error" in result

def test_calculator_unsupported_operations():
    calc = Calculator()
    
    # Bitwise operators not in allowed list
    result = calc.execute("5 | 3")
    assert "Error" in result
