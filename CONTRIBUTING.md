# Contributing to Validity

A big welcome and thank you for considering contributing to Validity project! Please read the following guidelines to make the process smooth and comfortable for both you and maintainers.


## Questions

You can leave a question about Validity in the [Discussions](https://github.com/amyasnikov/validity/discussions/) section. Please check out [documentation](https://validity.readthedocs.io) before asking a question.


## Issues

Issues should be used to report problems with the plugin, request a new feature, or to discuss potential changes before a PR is created. Some points for creating a good issue:
- Search for existing Issues and PRs before creating your own.
- If you're going to report a bug, always leave the steps to reproduce it inside the issue


## Pull Requests

PRs to Validity are welcome and can be a quick way to get your fix or improvement slated for the next release.

To be sure your PR will be accepted please **create an issue before making any code changes**. Describe your proposal and get an approval from the maintainer. After that you may make a PR related to this issue.

In general, PRs should:

- Close the specific issue opened **BEFORE** the PR
- Only fix/add the functionality described in the related issue
- Pass CI checks (linting and auto tests)
- Contain unit tests of the code being involved
- Contain new feature description in the `docs` folder (in the case of new functionality being added)

The overall Git Flow:

1. Fork the repository to your own Github account.
2. Clone the project to your machine.
3. Choose the branch for contributing. Bug fixes should be done in `master` branch while new functionality should be placed inside `devel` branch.
3. Create a feature related branch locally from the branch chosen at step 3.
4. Commit your changes.
6. Push changes to your fork.
7. Open a PR to the correct branch selected at point 3 (`devel` or `master`).


## Environment setup

You can easily set up your dev environment using `venv` and `docker compose`

```shell
# clone forked project
git clone https://github.com/<username>/validity/
cd validity

# create & activate virtual env
python3 -m venv env
source env/bin/activate

# install dev dependencies
pip install -r requirements/dev.txt

# set up pre-commit hook to run linting on every git commit
pre-commit install

# go to development folder to run project in docker
cd development

# Copy .env.example into .env and change the values if you need to
cp .env.example .env

# run the project
docker compose up -d --build

# get inside netbox web app container
docker compose exec -it netbox bash

# create database and admin user
./manage.py migrate
./manage.py createsuperuser

# run the tests
cd /plugin/validity
pytest
```
