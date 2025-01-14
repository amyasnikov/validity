import datetime
import inspect

import pytest

from validity.utils.logger import Logger, Message


@pytest.fixture(name="err")
def error_with_traceback():
    try:
        raise ValueError("error")
    except ValueError as e:
        return e


def test_logger(err):
    logger = Logger()
    logger.info("info-msg")
    logger.failure("failure-msg")
    logger.log_exception(err)

    assert len(logger.messages) == 3
    serialized_logs = [m.serialized for m in logger.messages]
    for log in serialized_logs:
        del log["time"]
    line_num = inspect.getsourcelines(error_with_traceback)[1] + 3
    assert serialized_logs == [
        {"status": "info", "message": "info-msg"},
        {"status": "failure", "message": "failure-msg"},
        {
            "status": "failure",
            "message": (
                "Unhandled error occured: `<class 'ValueError'>: error`\n```\n  "
                f'File "{__file__}", '
                f"""line {line_num}, in error_with_traceback\n    raise ValueError("error")\n\n```"""
            ),
        },
    ]


def test_as_context():
    with Logger() as logger:
        logger.info("msg1")
        assert logger.messages
    assert logger.messages == []


def test_script_id_context(timezone_now):
    timezone_now(datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc))
    logger = Logger()
    with logger.script_id("script1"):
        assert logger._script_id == "script1"
        logger.info("msg1")
        assert logger.messages == [
            Message(
                status="info",
                message="msg1",
                time=datetime.datetime(2000, 1, 2, 0, 0, tzinfo=datetime.timezone.utc),
                script_id="script1",
            )
        ]
    assert logger.messages == []
    assert logger._script_id is None
