from functools import partial as p
from unittest.mock import MagicMock, Mock

import pytest
from factories import (
    CompTestDBFactory,
    CompTestGitFactory,
    NameSetDBFactory,
    NameSetGitFactory,
    SerializerDBFactory,
    SerializerGitFactory,
)

from validity.models import base


@pytest.mark.parametrize(
    "factory, prop_name, expected_value",
    [
        (p(SerializerDBFactory, ttp_template="template"), "effective_template", "template"),
        (SerializerGitFactory, "effective_template", ""),
        (p(NameSetDBFactory, definitions="def f(): pass"), "effective_definitions", "def f(): pass"),
        (NameSetGitFactory, "effective_definitions", ""),
        (p(CompTestDBFactory, expression="1==2"), "effective_expression", "1==2"),
        (CompTestGitFactory, "effective_expression", ""),
    ],
)
@pytest.mark.django_db
def test_git_link_model(factory, prop_name, expected_value, monkeypatch):
    model = factory()
    mock_git = Mock(GitRepo=Mock(from_db=MagicMock()))
    monkeypatch.setattr(base, "git", mock_git)
    value = getattr(model, prop_name)
    if isinstance(value, Mock):
        assert value._extract_mock_name() == "mock.GitRepo.from_db().local_path.__truediv__().open().__enter__().read()"
        mock_git.GitRepo.from_db.assert_called_once_with(model.repo)
        mock_git.GitRepo.from_db.return_value.local_path.__truediv__.assert_called_once_with(model.file_path)
    else:
        assert value == expected_value
