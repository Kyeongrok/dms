from dmsclient.indices import Indices
from dmsclient.models import BaseModel
from dmsclient.templates import Templates
from dmsclient.utils import str_to_datetime


class Cluster(BaseModel):
    """
    Represents the configuration of an Isilon cluster
    """

    TEMPLATE = Templates.TEMPLATE_CONFIG
    INDEX = Indices.INDEX_CONFIG
    DOC_TYPE = 'cluster'

    def __init__(self, cluster_id, weight, available, updated_at, raw_export, perm_export, resim_export, output_export,
                 useroutput_export, raw_mount, perm_mount, resim_mount, output_mount, useroutput_mount, raw_share,
                 perm_share, resim_share, output_share, useroutput_share, nfs_host, smb_host):
        super(Cluster, self).__init__()
        self.cluster_id = cluster_id
        self.weight = weight
        self.available = available
        self.updated_at = str_to_datetime(updated_at)
        self.raw_export = raw_export
        self.perm_export = perm_export
        self.resim_export = resim_export
        self.output_export = output_export
        self.useroutput_export = useroutput_export
        self.raw_mount = raw_mount
        self.perm_mount = perm_mount
        self.resim_mount = resim_mount
        self.output_mount = output_mount
        self.useroutput_mount = useroutput_mount
        self.raw_share = raw_share
        self.perm_share = perm_share
        self.resim_share = resim_share
        self.output_share = output_share
        self.useroutput_share = useroutput_share
        self.nfs_host = nfs_host
        self.smb_host = smb_host

    @property
    def id(self):
        return self.cluster_id

    @property
    def timebased(self):
        return False
