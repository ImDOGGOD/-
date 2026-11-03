import ast

import pytest

from tools import _calc


def test_basic_ops():
    assert _calc(ast.parse("(3+5)*2", mode="eval")) == 16
    assert _calc(ast.parse("2**10", mode="eval")) == 1024
    assert _calc(ast.parse("10/4", mode="eval")) == 2.5


def test_rejected_expressions():
    for expr in ("__import__('os')", "open('x')", "a.b"):
        with pytest.raises(ValueError):
            _calc(ast.parse(expr, mode="eval"))
