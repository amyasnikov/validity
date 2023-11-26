import textwrap

import pytest
from django.core.exceptions import ValidationError
from factories import CompTestDSFactory, NameSetDSFactory, SelectorFactory, SerializerDSFactory


class BaseTestClean:
    factory: type
    right_kwargs: list[dict] = []
    wrong_kwargs: list[dict]

    @pytest.mark.django_db
    def test_clean_right(self, subtests):
        for i, kwargs in enumerate(self.right_kwargs):
            with subtests.test(id=i):
                model = self.factory(**kwargs)
                model.clean()

    @pytest.mark.django_db
    def test_clean_wrong(self, subtests):
        for i, kwargs in enumerate(self.wrong_kwargs):
            with subtests.test(id=i):
                model = self.factory(**kwargs)
                with pytest.raises(ValidationError):
                    model.clean()


class TestDBNameSet(BaseTestClean):
    factory = NameSetDSFactory
    right_definition = textwrap.dedent(
        """
            from collections import Counter

            __all__ = ['A', 'Counter', 'func']

            def func():
                pass

            class A:
                pass
        """
    )

    right_kwargs = [
        {"definitions": right_definition, "data_source": None, "data_file": None},
        {"definitions": "", "contents": right_definition},
    ]
    wrong_kwargs = [
        {"definitions": "a = 10", "data_source": None, "data_file": None},
        {"definitions": "some invalid syntax", "data_source": None, "data_file": None},
        {"definitions": "def some_func(): pass", "data_source": None, "data_file": None},
        {"definitions": right_definition, "data_source": None},
        {"definitions": right_definition, "data_file": None},
    ]


class TestSelector(BaseTestClean):
    factory = SelectorFactory

    wrong_kwargs = [{"name_filter": "qwerty", "dynamic_pairs": "NAME"}, {"name_filter": "invalidregex))))"}]


class TestSerializer(BaseTestClean):
    factory = SerializerDSFactory

    right_kwargs = [
        {
            "extraction_method": "TTP",
            "ttp_template": "interface {{ interface }}",
            "data_source": None,
            "data_file": None,
        },
        {"extraction_method": "YAML", "data_source": None, "data_file": None},
        {"extraction_method": "TTP", "ttp_template": "", "contents": "interface {{ interface }}"},
    ]
    wrong_kwargs = [
        {"extraction_method": "TTP", "ttp_template": "", "data_source": None, "data_file": None},
        {"extraction_method": "TTP", "ttp_template": "qwerty"},
        {"extraction_method": "TTP", "ttp_template": "qwerty", "data_source": None},
        {"extraction_method": "TTP", "ttp_template": "qwerty", "data_file": None},
        {"extraction_method": "YAML"},
    ]


class TestCompTest(BaseTestClean):
    factory = CompTestDSFactory

    right_kwargs = [{"expression": "a==1", "data_source": None, "data_file": None}, {}]
    wrong_kwargs = [
        {"expression": "a == b"},
        {"expression": "", "data_source": None, "data_file": None},
        {"expression": "a==b", "data_source": None},
        {"expression": "a==b", "data_file": None},
        {"expression": "a = 10 + 15", "data_source": None, "data_file": None},
        {"expression": "import itertools; a==b", "data_source": None, "data_file": None},
    ]
