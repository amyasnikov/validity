import os
import shutil
from pathlib import Path

import pytest

import validity


pytest.register_assert_rewrite("base")


@pytest.fixture
def tests_root():
    return Path(validity.__file__).parent.absolute() / "tests"


@pytest.fixture
def temp_file():
    file_paths = []

    def _temp_file(path, content):
        file_paths.append(str(path))
        with open(path, "w") as file:
            file.write(content)

    yield _temp_file
    for path in file_paths:
        os.remove(path)


@pytest.fixture
def temp_folder():
    folder_paths = []

    def _temp_folder(path):
        folder_paths.append(path)
        os.mkdir(path)

    yield _temp_folder
    for folder in folder_paths:
        shutil.rmtree(folder)


@pytest.fixture
def temp_file_and_folder(temp_folder, temp_file):
    def _temp_file_and_folder(base_dir, dirname, filename, file_content):
        temp_folder(base_dir / dirname)
        temp_file(base_dir / dirname / filename, file_content)

    return _temp_file_and_folder
