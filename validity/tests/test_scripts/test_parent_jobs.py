from unittest.mock import Mock

import pytest

from validity.scripts.parent_jobs import JobExtractor


class TestJobExtractor:
    def test_job(self):
        extractor = JobExtractor(_job=None)
        with pytest.raises(ValueError):
            extractor.job  # noqa: B018
        extractor = JobExtractor(_job=Mock())
        assert extractor.job == extractor._job

    def test_parent(self):
        extractor = JobExtractor(_job=Mock())
        assert extractor.parent.nesting_level == 1
        assert extractor.parent.parent.nesting_level == 2
        assert extractor.parent.job == extractor._job.dependency

    def test_parents(self):
        extractor = JobExtractor(_job=Mock())
        extractor._job.fetch_dependencies.return_value = [10, 20, 30]
        assert [p.job for p in extractor.parents] == [10, 20, 30]
        assert extractor.parents[0].nesting_level == 1

    def test_nesting_name(self):
        extractor = JobExtractor(_job=Mock())
        assert extractor.nesting_name == "Current"
        assert extractor.parent.nesting_name == "Parent"
        assert extractor.parent.parent.nesting_name == "x2 Parent"
