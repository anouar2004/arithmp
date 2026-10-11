# ArithmP

ArithmP is a small arithmetic expression parser and evaluator written in
Python. It supports calculations, comparisons, variables, user-defined
functions, and a command-line interface.

## Requirements

- Python 3.13 or newer

Install the project with your preferred Python package manager. For example,
with [uv](https://docs.astral.sh/uv/):

```console
uv sync
```

## Command-line usage

Evaluate one expression:

```console
arithmp "2 + 3 * 4"
14
```

Parse a file with one expression per line:

```console
arithmp --file calculations.arithmp
```

Start an interactive session:

```console
arithmp --interactive
> 2 + 3
5
```

The short options `-i` and `-f` are also available. File and interactive modes
can be combined; the file is parsed first, so definitions from the file are
available in the interactive session:

```console
arithmp --file functions.arithmp --interactive
```

An expression cannot be supplied together with `--file` or `--interactive`.

## Expression syntax

### Arithmetic

The parser supports:

| Syntax | Operation |
| --- | --- |
| `+x`, `-x` | Unary plus and minus |
| `x + y` | Addition |
| `x - y` | Subtraction |
| `x * y` | Multiplication |
| `x / y` | Division |
| `x % y` | Remainder |
| `x ^ y` | Exponentiation |

Parentheses can be used to control evaluation order:

```text
(2 + 3) * 4
```

Operators are evaluated with the usual precedence: exponentiation, unary
operators, multiplication/division/remainder, then addition/subtraction.
Comparisons have lower precedence than arithmetic operators.

### Comparisons and conditional expressions

The comparison operators are `==`, `!=`, `<`, `<=`, `>`, and `>=`. They
produce Boolean values, which can be used in a conditional expression:

```text
age >= 18 ? 1 : 0
```

### Variables

Assign a value with `=`. Assignments persist for the lifetime of a `Parser`
instance:

```text
radius = 3
area = pi * radius ^ 2
area
```

The predefined constants are `pi` and `e`.

### Functions

Define a function with a parameter list in square brackets and an arrow:

```text
square = [value] -> value ^ 2
square(5)
```

Multiple parameters are separated by commas:

```text
add = [left, right] -> left + right
add(2, 3)
```

Recursive functions are supported:

```text
factorial = [n] -> n <= 1 ? 1 : n * factorial(n - 1)
factorial(5)
```

The predefined functions are:

- `sin(x)`
- `cos(x)`
- `tan(x)`
- `sqrt(x)`
- `round(x)`
- `floor(x)`
- `ceil(x)`
- `print(x)`
- `exit()`

`print(x)` prints its argument and returns it. `exit()` ends an interactive
session.

## Multiple expressions

`Parser.parse()` accepts multiple expressions separated by newlines or
semicolons. Expressions are evaluated from left to right, and the result of
the last expression is returned:

```python
from arithmp.parser import Parser

parser = Parser()
result = parser.parse(
    """
    first = 10
    second = first * 2
    second + 2
    """
)

assert result == 22
```

Blank lines are ignored. A function or variable definition can therefore be
followed by an expression that uses it in the same call.

## Python API

Import `Parser` to evaluate expressions from Python:

```python
from arithmp.parser import Parser

parser = Parser()
print(parser.parse("sqrt(25) + 1"))
```

The `variables` and `functions` read-only mapping properties expose the
definitions currently held by a parser:

```python
parser.parse("answer = 42")
assert parser.variables["answer"] == 42
```

Parsing and evaluation errors are raised to the caller. For example, unknown
names raise `KeyError`, invalid syntax raises a Lark parsing exception, and
division by zero raises `ZeroDivisionError`.
