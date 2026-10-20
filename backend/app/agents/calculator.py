"""Calculator: evaluates arithmetic locally by walking the AST. Never calls eval()."""

import ast
import math
import operator

from app.protocol import reply, result

NAME = "calculator"
TASK = "calculate"

_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MAX_EXPONENT = 1000
MAX_MAGNITUDE = 1e300


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ValueError("Exponent is too large.")
        value = _BINARY[type(node.op)](left, right)
        if isinstance(value, complex) or abs(value) > MAX_MAGNITUDE:
            raise ValueError("Result is not a real number in range.")
        return value
    raise ValueError("Use numbers and + - * / % ^ ( ) only.")


def calculate(expr: str) -> int | float:
    try:
        tree = ast.parse(expr.replace("^", "**"), mode="eval")
        value = _eval(tree.body)
    except (SyntaxError, RecursionError):
        raise ValueError("Expression is incomplete or malformed.") from None
    except ZeroDivisionError:
        raise ValueError("Division by zero.") from None
    except OverflowError:
        raise ValueError("Result is too large.") from None
    if not math.isfinite(value):
        raise ValueError("Result is not a finite number.")
    return int(value) if float(value).is_integer() else float(f"{value:.15g}")


async def handle(msg):
    yield reply(msg, "return_calculation", result("text", str(calculate(msg.content))))
