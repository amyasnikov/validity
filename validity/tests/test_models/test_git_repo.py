from functools import partial

import pytest
from factories import GitRepoFactory

from validity.models import GitRepo


@pytest.mark.django_db
def test_password():
    repo = GitRepo(
        name="r1",
        git_url="http://repo.url/path",
        web_url="http://repo.url/path",
        device_config_path="somepath",
        username="adm",
    )
    repo.password = "some_password"
    repo.save()
    db_repo = GitRepo.objects.get(pk=repo.pk)
    assert db_repo.password == repo.password


@pytest.mark.parametrize(
    "factory, expected_url",
    [
        (GitRepoFactory, GitRepoFactory.git_url),
        (
            partial(GitRepoFactory, username="admin", password="1234", git_url="http://some.url/path"),
            "http://admin:1234@some.url/path",
        ),
    ],
)
@pytest.mark.django_db
def test_full_git_url(factory, expected_url):
    repo = factory()
    assert repo.full_git_url == expected_url
