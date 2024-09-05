import uuid

import pytest
from factories import RunTestsJobFactory

from validity.scripts.data_models import RequestInfo, RunTestsParams


@pytest.fixture
def runtests_params():
    return RunTestsParams(request=RequestInfo(id=uuid.uuid4(), user_id=1))


@pytest.fixture
def full_runtests_params(runtests_params):
    job = RunTestsJobFactory()
    return runtests_params.with_job_info(job)
