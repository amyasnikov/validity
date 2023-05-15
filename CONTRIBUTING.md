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

To be sure your PR would be accepted please **create an issue before making any code changes**. Describe your proposal and get an approval from the maintainer. After that you may make a PR related to this issue.

In general, PRs should:

- Close the specific issue opened **BEFORE** the PR
- Only fix/add the functionality described in the related issue
- Pass CI checks (black, isort, flake8, pytest)
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

You can easily set up your dev environment using `docker compose`

1. Clone the project.
2. Go to `development` folder.
3. Copy `.env.example` into `.env` and change the values if you need.
4. Run the project via `docker compose up -d --build`
5. Connect to `netbox` container, run the migrations and issue script linking<br/>
```
docker compose exec -it netbox bash
./manage.py migrate
./manage.py linkscripts
./manage.py createsuperuser
```
6. Now dev project is ready to use, you can reach it via browser at `http://127.0.0.1:8000`
7. To run linters and tests issue<br/>
```
cd /plugin/validity
black validity
isort validity
flake8 validity
pytest
```
