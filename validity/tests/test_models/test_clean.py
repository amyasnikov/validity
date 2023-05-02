import textwrap

import pytest
from django.core.exceptions import ValidationError
from factories import CompTestGitFactory, GitRepoFactory, NameSetGitFactory, SelectorFactory, SerializerGitFactory


@pytest.mark.django_db
def test_only_one_default_repo():
    GitRepoFactory(default=True)
    with pytest.raises(ValidationError):
        repo = GitRepoFactory.build(default=True)
        repo.clean()


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


class TestNameSet(BaseTestClean):
    factory = NameSetGitFactory
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

    right_kwargs = [{"definitions": right_definition, "repo": None, "file_path": ""}]
    wrong_kwargs = [
        {"definitions": "a = 10", "repo": None, "file_path": ""},
        {"definitions": "some invalid syntax", "repo": None, "file_path": ""},
        {"definitions": "def some_func(): pass", "repo": None, "file_path": ""},
        {"definitions": right_definition, "repo": None},
        {"definitions": right_definition, "file_path": ""},
    ]


class TestSelector(BaseTestClean):
    factory = SelectorFactory

    wrong_kwargs = [{"name_filter": "qwerty", "dynamic_pairs": "NAME"}, {"name_filter": "invalidregex))))"}]


class TestSerializer(BaseTestClean):
    factory = SerializerGitFactory

    right_kwargs = [
        {"extraction_method": "TTP", "ttp_template": "interface {{ interface }}", "repo": None, "file_path": ""},
        {"extraction_method": "YAML", "repo": None, "file_path": ""},
    ]
    wrong_kwargs = [
        {"extraction_method": "TTP", "ttp_template": "", "repo": None, "file_path": ""},
        {"extraction_method": "TTP", "ttp_template": "qwerty", "file_path": ""},
        {"extraction_method": "YAML"},
    ]


class TestTest(BaseTestClean):
    factory = CompTestGitFactory

    right_kwargs = [{"expression": "a==1", "repo": None, "file_path": ""}, {}]
    wrong_kwargs = [{"expression": "a==b", "repo": None}, {"expression": "a = 10 + 15", "repo": None, "file_path": ""}]
