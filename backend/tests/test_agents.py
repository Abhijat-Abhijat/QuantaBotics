import json
from pathlib import Path

import pytest

from app.agents.calculator import calculate
from app.agents.data_visualizer import parse_chart_data
from app.orchestrator import route

CASES = json.loads((Path(__file__).parents[2] / "tests" / "routing_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[c["input"] for c in CASES])
def test_route_matches_shared_cases(case):
    assert route(case["input"]) == (case["agent"], case["text"])


@pytest.mark.parametrize(
    ("expr", "expected"),
    [("5 * (2 + 3)", 25), ("2 + 3 * 4", 14), ("-2 ^ 2", -4), ("2 ^ 3 ^ 2", 512), ("0.1 + 0.2", 0.3), ("10 % 4 - -1", 3), ("7 / 2", 3.5)],
)
def test_calculate(expr, expected):
    assert calculate(expr) == expected


@pytest.mark.parametrize(
    "expr",
    ["1 / 0", "(1 + 2", "2 +", "2 3", "__import__('os')", "(1).__class__", "2 ^ 99999", "(-8) ^ 0.5", "1e400", "(" * 500 + "1" + ")" * 500],
)
def test_calculate_rejects_unsafe_or_invalid(expr):
    with pytest.raises(ValueError):
        calculate(expr)


def test_parse_chart_data():
    assert parse_chart_data('{"A": 10, "B": "20"}') == [{"label": "A", "value": 10.0}, {"label": "B", "value": 20.0}]
    assert parse_chart_data("{'Q1': 5}") == [{"label": "Q1", "value": 5.0}]
    for bad in ("Q1 sales 10", "[1, 2]", '{"A": "x"}', '{"A": true}', "{}"):
        assert parse_chart_data(bad) is None
