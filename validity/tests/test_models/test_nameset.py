import inspect
import textwrap

import pytest
from factories import NameSetDBFactory


class TestExtract:
    def use_builtin():
        return int("5")

    def use_import_stdlib():
        return floor(5.9)  # noqa

    def use_extra_global():
        return divide_by_2(10)  # noqa

    def nameset_with_fn(self, fn, imports):
        all_ = f'__all__ = ["{fn.__name__}"]'
        func_code = textwrap.dedent(inspect.getsource(fn))
        code_lines = imports + [all_] + [func_code]
        definitions = "\n".join(code_lines)
        return NameSetDBFactory(definitions=definitions)

    @pytest.mark.parametrize("fn", [use_builtin, use_import_stdlib, use_extra_global])
    @pytest.mark.django_db
    def test_extract(self, fn):
        imports = ["from math import floor"]
        nameset = self.nameset_with_fn(fn, imports)
        definitions = nameset.extract(extra_globals={"divide_by_2": lambda x: x // 2})
        func = definitions[fn.__name__]
        assert func() == 5
