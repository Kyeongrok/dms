from datetime import datetime

from dmsclient.indices import Indices
from dmsclient.models import BaseModel
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class AsdmOutput(BaseModel):
    """
    Represents a ASDM Output
    """

    TEMPLATE = Templates.TEMPLATE_RESIM
    INDEX = Indices.timebased(Indices.INDEX_RESIM_PREFIX)
    DOC_TYPE = 'asdmoutput'

    PROTECTED_ATTRIBUTES = ['asdmoutput_id',
                            'segment_id',
                            'sensor_versions',
                            'asdm_version',
                            'cluster_id',
                            'created_at',
                            'updated_at',
                            'nfs_host',
                            'smb_host',
                            'dat_file',
                            'mat_file',
                            'smb_share',
                            'path']

    def __init__(self, asdmoutput_id, segment_id, sensor_versions, asdm_version, cluster_id,
                 created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
                 nfs_host=None, smb_host=None, dat_file=None, mat_file=None, smb_share=None,
                 path=None, **kwargs):
        super(AsdmOutput, self).__init__(**kwargs)
        self.asdmoutput_id = asdmoutput_id
        self.segment_id = segment_id
        self.sensor_versions = sensor_versions
        self.asdm_version = asdm_version
        self.cluster_id = cluster_id
        self.created_at = str_to_datetime(created_at)
        self.updated_at = str_to_datetime(updated_at)
        self.nfs_host = nfs_host
        self.smb_host = smb_host
        self.dat_file = dat_file
        self.mat_file = mat_file
        self.smb_share = r"\\" + str(smb_host) + str(path) if not smb_share else smb_share
        self.path = path
        self.extra_fields = kwargs

    @property
    def id(self):
        return self.asdmoutput_id

    @property
    def timebased(self):
        return True
