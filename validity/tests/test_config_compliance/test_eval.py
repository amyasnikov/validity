import json
from contextlib import nullcontext

import pytest
from deepdiff.serialization import json_dumps
from simpleeval import InvalidExpression

from validity.config_compliance.eval import ExplanationalEval
from validity.config_compliance.exceptions import EvalError


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


@pytest.mark.parametrize(
    "expression, explanation, error",
    [
        pytest.param("5 + 5 == 10", [("5 + 5", 10), ("5 + 5 == 10", True)], None, id="5+5"),
        pytest.param(EXPR_1, EXPLANATION_1, None, id="EXPR_1"),
        pytest.param(EXPR_2, EXPLANATION_2, None, id="EXPR_2"),
        pytest.param("some invalid syntax", [], EvalError, id="invalid syntax"),
        pytest.param("def f(): pass", [], InvalidExpression, id="invalif expression"),
    ],
)
def test_explanation(expression, explanation, error):
    evaluator = ExplanationalEval()
    context = nullcontext() if error is None else pytest.raises(error)
    with context:
        evaluator.eval(expression)
        # deepdiff dict may have complex objects
        assert json.loads(json_dumps(evaluator.explanation)) == json.loads(json_dumps(explanation))
