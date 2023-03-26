import ast

import deepdiff
from simpleeval import EvalWithCompoundTypes, InvalidExpression

from ..exceptions import EvalError


class ExplanationalEval(EvalWithCompoundTypes):

    do_not_explain = (ast.Constant, ast.Name, ast.Attribute, ast.Expr)

    def __init__(self, operators=None, functions=None, names=None, deepdiff_types=None):
        if deepdiff_types is None:
            deepdiff_types = (list, dict, set, frozenset, tuple)
        self.deepdiff_types = deepdiff_types
        self.explanation = []
        self._deepdiff = []
        super().__init__(operators, functions, names)

    def _eval(self, node):
        result = super()._eval(node)
        unparsed = ast.unparse(node)
        if not isinstance(node, self.do_not_explain) and str(result) != unparsed and unparsed:
            self.explanation.append((unparsed, result))
        self.explanation.extend(self._deepdiff)
        self._deepdiff = []
        return result

    def _eval_compare(self, node):
        right = self._eval(node.left)
        to_return = True
        for i, (operation, comp) in enumerate(zip(node.ops, node.comparators), 1):
            if not to_return:
                break
            left = right
            right = self._eval(comp)
            to_return = self.operators[type(operation)](left, right)
            if isinstance(left, self.deepdiff_types) and isinstance(right, self.deepdiff_types) and not to_return:
                diff_name = "Deepdiff for previous comparison"
                if len(node.ops) > 1:
                    diff_name += f" [#{i}]"
                self._deepdiff.append((diff_name, deepdiff.DeepDiff(left, right).to_dict()))
        return to_return

    def eval(self, expr):
        self.explanation = []
        try:
            return super().eval(expr)
        except InvalidExpression:
            raise
        except Exception as e:
            raise EvalError(e) from e
