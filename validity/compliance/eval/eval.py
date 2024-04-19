import ast
import re
from typing import Literal

import deepdiff
import simpleeval

from validity.utils.misc import reraise
from ..exceptions import EvalError
from . import default_nameset, eval_defaults


class DictCompWithElt(ast.DictComp):
    @property
    def elt(self):
        return ast.Tuple(elts=[self.key, self.value])


class EvalWithCompoundTypes(simpleeval.EvalWithCompoundTypes):
    """
    This class provides support for DictComp and SetComp
    """

    def __init__(self, operators=None, functions=None, names=None):
        super().__init__(operators, functions, names)
        self.nodes |= {ast.DictComp: self._eval_dictcomp, ast.SetComp: lambda node: set(self._eval_comprehension(node))}

    def _eval_dictcomp(self, node):
        node = DictCompWithElt(**node.__dict__)
        return dict(self._eval_comprehension(node))


class ExplanationalEval(EvalWithCompoundTypes):
    do_not_explain = (ast.Constant, ast.Name, ast.Attribute, ast.Expr)

    def __init__(
        self,
        operators=None,
        functions=None,
        names=None,
        deepdiff_types=None,
        *,
        load_defaults=False,
        verbosity: Literal[0, 1, 2] = 2,
    ):
        self.verbosity = verbosity
        deepdiff_types = deepdiff_types or (list, dict, set, frozenset, tuple)
        if verbosity < 2:
            # disable deepdiff explanation
            deepdiff_types = ()
        self.deepdiff_types = deepdiff_types
        self.explanation = []
        self._deepdiff = []
        if load_defaults:
            operators, functions, names = self._load_defaults(operators=operators, functions=functions, names=names)
        super().__init__(operators, functions, names)

    def _load_defaults(self, /, **kwargs):
        kwargs = {k: {} if v is None else v for k, v in kwargs.items()}
        kwargs["functions"] = {name: getattr(default_nameset, name) for name in default_nameset.__all__} | kwargs[
            "functions"
        ]
        kwargs["operators"] = eval_defaults.DEFAULT_OPERATORS | kwargs["operators"]
        kwargs["names"] = eval_defaults.DEFAULT_NAMES | kwargs["names"]
        return kwargs["operators"], kwargs["functions"], kwargs["names"]

    def _eval(self, node):
        result = super()._eval(node)
        if self.verbosity < 1:
            return result
        unparsed = ast.unparse(node)
        if not isinstance(node, self.do_not_explain) and str(result) != unparsed and unparsed:
            self.explanation.append((self._format_unparsed(unparsed), result))
        self.explanation.extend(self._deepdiff)
        self._deepdiff = []
        return result

    def _format_unparsed(self, unparsed) -> str:
        return re.sub(r" *\\n *", "", unparsed)

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
        with reraise(Exception, EvalError):
            return super().eval(expr)
