from unittest.mock import Mock

import pytest
from extras.scripts import Script


@pytest.fixture
def mock_script_logging(monkeypatch):
    for log_func in ["log_debug", "log_info", "log_failure", "log_success", "log_warning"]:
        monkeypatch.setattr(Script, log_func, Mock())
