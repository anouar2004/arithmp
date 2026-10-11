"""Arithmetic expression parser and evaluator."""

import math
import operator
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, NoReturn, cast

from lark import Lark, Token, Tree

_builtins = {
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "div": operator.truediv,
    "mod": operator.mod,
    "equal": operator.eq,
    "not_equal": operator.ne,
    "less": operator.lt,
    "less_equal": operator.le,
    "greater": operator.gt,
    "greater_equal": operator.ge,
}


def _exit() -> NoReturn:
    raise SystemExit


class ParserException(Exception):
    """
    Custom exception for parser errors.
    """


class UndefinedVariableException(ParserException):
    """
    Exception raised when an undefined variable is accessed.
    """

    def __init__(self, variable_name: str) -> None:
        """
        Initialize the exception with the variable name.
        """
        super().__init__(f"undefined variable '{variable_name}'")
        self.variable_name = variable_name


class UndefinedFunctionException(ParserException):
    """
    Exception raised when an undefined function is called.
    """

    def __init__(self, function_name: str) -> None:
        """
        Initialize the exception with the function name.
        """
        super().__init__(f"undefined function '{function_name}'")
        self.function_name = function_name


class BadFunctionCallException(ParserException):
    """
    Exception raised when a function is called with incorrect arguments.
    """

    def __init__(self, function_name: str, message: str) -> None:
        """
        Initialize the exception with the function name and an error message.
        """
        super().__init__(f"bad function call '{function_name}': {message}")
        self.function_name = function_name
        self.message = message


class Parser:
    """
    Parser for arithmetic expressions, supporting variables, functions, and basic
    arithmetic operations.
    """

    def __init__(self) -> None:
        """
        Initialize the parser and set up built-in variables and functions.
        """
        self.parser = Lark(
            Path(__file__).parent.joinpath("arithmp.lark").read_text(), parser="lalr"
        )

        self._variables: dict[str, float] = {"pi": math.pi, "e": math.exp(1)}
        self._functions: dict[str, Callable[..., float | None]] = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "round": round,
            "floor": math.floor,
            "ceil": math.ceil,
            "print": print,
            "exit": _exit,
        }

    @property
    def variables(self) -> Mapping[str, float]:
        """Variables currently defined."""
        return self._variables

    @property
    def functions(self) -> Mapping[str, Callable[..., float | None]]:
        """Functions currently defined."""
        return self._functions

    def _eval_as_float(
        self, tree: Tree[Token] | Token, variables: Mapping[str, float]
    ) -> float:
        result = self._eval(tree, variables)
        if result is None:
            raise ValueError("Expected a numeric value, got None")
        return result

    def _eval(
        self, tree: Tree[Token] | Token, variables: Mapping[str, float]
    ) -> float | None:
        if isinstance(tree, Token):
            if tree.type == "NUMBER":
                try:
                    return int(tree.value)
                except ValueError:
                    return float(tree.value)
            else:
                # should never occur, there are no other token types in the grammar
                raise ParserException(f"unexpected token type: {tree.type}")

        match tree.data:
            case "number":
                return self._eval_as_float(tree.children[0], variables)
            case "variable":
                name = cast(Token, tree.children[0]).value
                if name in variables:
                    return variables[name]
                elif name in self._variables:
                    return self._variables[name]
                else:
                    raise UndefinedVariableException(name)
            case "function_call":
                # retrieve function name and check if it exists
                func_name = cast(Token, tree.children[0]).value
                if func_name not in self._functions:
                    raise UndefinedFunctionException(func_name)
                function = self._functions[func_name]

                # retrieve the arguments and check the number
                children: list[Token | Tree[Token]] = []
                if (arguments := cast(Tree[Token], tree.children[1])) is not None:
                    children = arguments.children

                try:
                    return function(
                        *(self._eval_as_float(child, variables) for child in children)
                    )
                except TypeError as e:
                    raise BadFunctionCallException(func_name, str(e)) from e

            case "variable_assignment":
                var_name = cast(str, cast(Token, tree.children[0]).value)
                var_value = self._eval_as_float(tree.children[1], variables)
                self._variables[var_name] = var_value
                return var_value
            case "function_assignment":
                func_name = cast(str, cast(Token, tree.children[0]).value)

                func_tree = cast(Tree[Token], tree.children[1])
                func_params = []
                if parameters := cast(Tree[Token], func_tree.children[0]):
                    func_params = [
                        cast(str, cast(Token, child).value)
                        for child in parameters.children
                    ]
                func_body = cast(Tree[Token], func_tree.children[1])

                def _call_fn(*args: Any) -> float | None:  # ruff: ignore[any-type]
                    if len(args) != len(func_params):
                        raise BadFunctionCallException(
                            func_name,
                            f"incorrect number of arguments, expected {len(func_params)}, got {len(args)}",
                        )
                    return self._eval(
                        func_body,
                        {**variables, **dict(zip(func_params, args, strict=True))},
                    )

                self._functions[func_name] = _call_fn

            case "ternary":
                condition = self._eval(tree.children[0], variables)
                if condition:
                    return self._eval(tree.children[1], variables)
                else:
                    return self._eval(tree.children[2], variables)
            case (
                "add"
                | "sub"
                | "mul"
                | "div"
                | "mod"
                | "equal"
                | "not_equal"
                | "less"
                | "less_equal"
                | "greater"
                | "greater_equal"
            ):
                return _builtins[tree.data](
                    self._eval_as_float(tree.children[0], variables),
                    self._eval_as_float(tree.children[1], variables),
                )
            case "pos":
                return self._eval_as_float(tree.children[0], variables)
            case "neg":
                return -self._eval_as_float(tree.children[0], variables)
            case "power":
                return self._eval_as_float(
                    tree.children[0], variables
                ) ** self._eval_as_float(tree.children[1], variables)
            case _:
                # should never occur
                raise ParserException(f"unexpected tree data: {tree.data}")

    def parse(self, expression: str) -> float | None:
        """
        Parse and evaluate an arithmetic expression.

        Args:
            expression: The arithmetic expression to parse and evaluate.

        Returns:
            The result of the evaluated expression, or None if no expressions were
            provided.
        """
        # the ; and \n are not part of the grammar, we treat them here
        expressions = [
            expression
            for expr in expression.replace(";", "\n").split("\n")
            if (expression := expr.strip())
        ]

        return_value: float | None = None
        for expression in expressions:
            try:
                return_value = self._eval(self.parser.parse(expression), {})
            except ParserException:
                raise
            except Exception as e:
                raise ParserException(
                    f"Unexpected error parsing expression '{expression}': {e}"
                ) from e

        return return_value
