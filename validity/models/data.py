from core.models import DataFile, DataSource
from validity.managers import VDataFileQS


class VDataFile(DataFile):
    objects = VDataFileQS.as_manager()

    json_fields = (
        'id', 'data', 'path', 'size', 'hash', 'created', 'last_updated'
    )

    class Meta:
        proxy = True


class VDataSource(DataSource):
    class Meta:
        proxy = True
