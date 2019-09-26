from datetime import datetime

from dmsclient.models import StrEnum
from dmsclient.models.reader import Reader


class USBReader(Reader):
    """
    Represents a USB reader located in an upload station
    """
    DOC_TYPE = 'usb_reader'

    class MountState(StrEnum):
        MOUNTED = 'mounted'
        UNMOUNTED = 'unmounted'

    def __init__(self, reader_id, hostname, device, mount_state=MountState.UNMOUNTED,
                 ingest_state=Reader.IngestState.IDLE,
                 message="", mount="", port="", status=Reader.Status.EMPTY,
                 updated_at=datetime.utcnow(), *args, **kwargs):
        # status attribute not applicable to this class, but pass it's default value to parent class
        super().__init__(reader_id, hostname, device, status,
                         ingest_state, message, mount, port,
                         updated_at, *args, **kwargs)

        self.mount_state = USBReader.MountState(mount_state)
