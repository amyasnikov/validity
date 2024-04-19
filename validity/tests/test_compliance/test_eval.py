import ast
import json
import operator
from contextlib import nullcontext

import pytest
from deepdiff.serialization import json_dumps

from validity.compliance.eval import EvalWithCompoundTypes, ExplanationalEval, default_nameset, eval_defaults
from validity.compliance.exceptions import EvalError


EXPR_1 = '{"param_1": "val_1", "param_2": "val_2"} == {"param_1": "val_1"}'
EXPLANATION_1 = [
    ["{'param_1': 'val_1', 'param_2': 'val_2'} == {'param_1': 'val_1'}", False],
    ["Deepdiff for previous comparison", {"dictionary_item_removed": ["root['param_2']"]}],
]

EXPR_2 = "[10, 11] == [10, 11] == [10, 12]"
EXPLANATION_2 = [
    ("[10, 11] == [10, 11] == [10, 12]", False),
    ("Deepdiff for previous comparison [#2]", {"values_changed": {"root[1]": {"new_value": 12, "old_value": 11}}}),
]

JQ_EXPR = "jq.first('. | mkarr(.a)', {'a': 1}) == {'a': [1]}"
JQ_EXPLANATION = [
    ("jq.first('. | mkarr(.a)', {'a': 1})", {"a": [1]}),
    ("jq.first('. | mkarr(.a)', {'a': 1}) == {'a': [1]}", True),
]


@pytest.mark.parametrize(
    "expression, explanation, error",
    [
        pytest.param("5 + 5 == 10", [("5 + 5", 10), ("5 + 5 == 10", True)], None, id="5+5"),
        pytest.param(EXPR_1, EXPLANATION_1, None, id="EXPR_1"),
        pytest.param(EXPR_2, EXPLANATION_2, None, id="EXPR_2"),
        pytest.param("some invalid syntax", [], EvalError, id="invalid syntax"),
        pytest.param("def f(): pass", [], EvalError, id="invalid expression"),
        pytest.param(JQ_EXPR, JQ_EXPLANATION, None, id="jq_expr"),
    ],
)
def test_explanation(expression, explanation, error):
    evaluator = ExplanationalEval(load_defaults=True)
    context = nullcontext() if error is None else pytest.raises(error)
    with context:
        evaluator.eval(expression)
        # deepdiff dict may have complex objects
        assert json.loads(json_dumps(evaluator.explanation)) == json.loads(json_dumps(explanation))


DEF_FUNCTIONS = {name: getattr(default_nameset, name) for name in default_nameset.__all__}
DEF_NAMES = eval_defaults.DEFAULT_NAMES
DEF_OPS = eval_defaults.DEFAULT_OPERATORS

EXTRA_FUNCTIONS = {"func": lambda x: x * x}
EXTRA_NAMES = {"obj": 10}
EXTRA_OPS = {ast.BitOr: operator.or_}


@pytest.mark.parametrize(
    "init_kwargs, expected_names, expected_functions, expected_operators",
    [
        ({"load_defaults": True}, DEF_NAMES, DEF_FUNCTIONS, DEF_OPS),
        (
            {"load_defaults": True, "functions": EXTRA_FUNCTIONS, "operators": EXTRA_OPS, "names": EXTRA_NAMES},
            DEF_NAMES | EXTRA_NAMES,
            DEF_FUNCTIONS | EXTRA_FUNCTIONS,
            DEF_OPS | EXTRA_OPS,
        ),
        (
            {"functions": EXTRA_FUNCTIONS, "operators": EXTRA_OPS, "names": EXTRA_NAMES},
            EXTRA_NAMES,
            EXTRA_FUNCTIONS,
            EXTRA_OPS,
        ),
    ],
)
def test_load_defaults(init_kwargs, expected_names, expected_functions, expected_operators):
    ev = ExplanationalEval(**init_kwargs)
    assert ev.names == expected_names
    assert ev.operators == expected_operators
    assert ev.functions == expected_functions


@pytest.mark.parametrize(
    "expression, result",
    [
        ("{i: i for i in range(3)}", {0: 0, 1: 1, 2: 2}),
        ("{2 * i: 3 * i for i in range(1, 3)}", {2: 3, 4: 6}),
        ("{str(i): 1 for i in range(3) if i >= 2}", {"2": 1}),
        ("{a:a for a in [1,2,3,4,5] if a <= 3 and a > 1 }", {2: 2, 3: 3}),
        ("{a:a+b+c for a, (b, c) in ((1,(1,1)),(3,(2,2)))}", {1: 3, 3: 7}),
        (
            "{str(a)+str(b): a+b for a in range(2) for b in range(3)}",
            {"00": 0, "01": 1, "02": 2, "10": 1, "11": 2, "12": 3},
        ),
    ],
)
def test_dict_comp(expression, result):
    ev = EvalWithCompoundTypes(functions={"range": range, "str": str})
    assert ev.eval(expression) == result


@pytest.mark.parametrize(
    "expression, result",
    [
        ("{i for i in range(3)}", {0, 1, 2}),
        ("{i*2 for i in range(3)}", {0, 2, 4}),
        ("{i*2 for i in range(3) if i > 1}", {4}),
    ],
)
def test_set_comp(expression, result):
    ev = EvalWithCompoundTypes(functions={"range": range})
    assert ev.eval(expression) == result
