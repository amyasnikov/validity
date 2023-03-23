from pathlib import Path

import tomli

import validity


def test_version():
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with pyproject_path.open(mode="rb") as f:
        pyproject_content = tomli.load(f)
    assert validity.config.version == pyproject_content["project"]["version"]
