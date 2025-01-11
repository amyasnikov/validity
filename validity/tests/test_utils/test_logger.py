import pytest

from validity.utils.logger import Logger


@pytest.fixture
def error_with_traceback():
    # moving this function up/down will cause the test to fail
    try:
        raise ValueError("error")
    except ValueError as e:
        return e


def test_logger(error_with_traceback):
    logger = Logger()
    logger.info("info-msg")
    logger.failure("failure-msg")
    logger.log_exception(error_with_traceback)

    assert len(logger.messages) == 3
    serialized_logs = [m.serialized for m in logger.messages]
    for log in serialized_logs:
        del log["time"]
    assert serialized_logs == [
        {"status": "info", "message": "info-msg"},
        {"status": "failure", "message": "failure-msg"},
        {
            "status": "failure",
            "message": (
                "Unhandled error occured: `<class 'ValueError'>: error`\n```\n  "
                f'File "{__file__}", '
                """line 10, in error_with_traceback\n    raise ValueError("error")\n\n```"""
            ),
        },
    ]
