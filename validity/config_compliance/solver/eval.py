import ast

import deepdiff
from simpleeval import EvalWithCompoundTypes, InvalidExpression

from ..exceptions import EvalError


class ExplanationalEval(EvalWithCompoundTypes):

    do_not_explain = (ast.Constant, ast.Name, ast.Attribute)

    def __init__(self, operators=None, functions=None, names=None, deepdiff_types=None):
        if deepdiff_types is None:
            deepdiff_types = (list, dict, set, frozenset, tuple)
        self.deepdiff_types = deepdiff_types
        self.explanation = []
        super().__init__(operators, functions, names)

    def _eval(self, node):
        result = super()._eval(node)
        unparsed = ast.unparse(node)
        if not isinstance(node, self.do_not_explain) and str(result) != unparsed and unparsed:
            last_expr = next(iter(self.explanation[-1:]), None)
            if last_expr != unparsed and last_expr != (new_expr := (unparsed, result)):
                self.explanation.append(new_expr)
        return result

    def _eval_compare(self, node):
        right = self._eval(node.left)
        to_return = True
        for operation, comp in zip(node.ops, node.comparators):
            if not to_return:
                break
            left = right
            right = self._eval(comp)
            if isinstance(left, self.deepdiff_types) and isinstance(right, self.deepdiff_types):
                self.explanation.append(("Deepdiff between 2 previous lines", deepdiff.DeepDiff(left, right).to_dict()))
            to_return = self.operators[type(operation)](left, right)
        return to_return

    def eval(self, expr):
        self.explanation = []
        try:
            return super().eval(expr)
        except InvalidExpression:
            raise
        except Exception as e:
            raise EvalError(e) from e
