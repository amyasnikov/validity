import textwrap
from contextlib import nullcontext

import pytest
from django.core.exceptions import ValidationError
from factories import CommandFactory, CompTestDSFactory, NameSetDSFactory, SelectorFactory, SerializerDSFactory

from validity.models import Poller


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
            "template": "interface {{ interface }}",
            "data_source": None,
            "data_file": None,
        },
        {"extraction_method": "YAML", "data_source": None, "data_file": None},
        {"extraction_method": "TTP", "template": "", "contents": "interface {{ interface }}"},
    ]
    wrong_kwargs = [
        {"extraction_method": "TTP", "template": "", "data_source": None, "data_file": None},
        {"extraction_method": "TTP", "template": "qwerty"},
        {"extraction_method": "TTP", "template": "qwerty", "data_source": None},
        {"extraction_method": "TTP", "template": "qwerty", "data_file": None},
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


class TestPoller:
    @pytest.mark.parametrize(
        "connection_type, command_type, is_valid", [("netmiko", "CLI", True), ("netmiko", "netconf", False)]
    )
    @pytest.mark.django_db
    def test_match_command_type(self, connection_type, command_type, is_valid):
        command = CommandFactory(type=command_type)
        ctx = nullcontext() if is_valid else pytest.raises(ValidationError)
        with ctx:
            Poller.validate_commands(connection_type=connection_type, commands=[command])

    @pytest.mark.parametrize(
        "retrive_config, is_valid",
        [
            ([True], True),
            ([False], True),
            ([False, True], True),
            ([False, False, False], True),
            ([True, True], False),
            ([True, False, True], False),
        ],
    )
    @pytest.mark.django_db
    def only_one_config_command(self, retrive_config, is_valid):
        commands = [CommandFactory(type=t) for t in retrive_config]
        ctx = nullcontext() if is_valid else pytest.raises(ValidationError)
        with ctx:
            Poller.validate_commands(connection_type="CLI", commands=commands)
