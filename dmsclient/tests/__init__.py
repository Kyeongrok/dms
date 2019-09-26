import configparser
import os
import unittest

import datetime

from dmsclient.client import DMSClient
from dmsclient.models.cluster import Cluster


class BaseTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        self.skip_tests = False
        self._get_config()

    def _get_config(self):
        config_file = os.environ.get('TEST_CONFIG_FILE',
                                     os.path.join(os.getcwd(), "tests/test.conf"))
        config = configparser.ConfigParser()
        config.read(config_file)
        self.config = config
        if config.has_section('func_test'):
            self.endpoint = config.get('func_test', 'endpoint')
            self.user = config.get('func_test', 'user')
            self.password = config.get('func_test', 'password')
        else:
            self.skip_tests = True

    def _get_client(self):
        return DMSClient(
            es_endpoint=self.endpoint,
            es_user=self.user,
            es_password=self.password,
            create_templates=True,
            verify_templates=True,
            initial_sync=False
        )

    def setUp(self):
        super(BaseTestCase, self).setUp()
        if self.skip_tests:
            self.skipTest('SKIPPING FUNCTIONAL TESTS DUE TO NO CONFIG')

        self.client = self._get_client()

        cluster = Cluster(cluster_id='amst-cl01',
                          weight=1,
                          available=True,
                          updated_at=datetime.datetime.utcnow(),
                          raw_export='/raw/export',
                          perm_export='/perm/export',
                          resim_export='/resim/export',
                          output_export='/output/export',
                          useroutput_export='/useroutput/export',
                          raw_mount='/ifs/z1/amst-cl01/raw',
                          perm_mount='/ifs/z1/amst-cl01/perm',
                          resim_mount='/ifs/z1/amst-cl01/resim',
                          output_mount='/ifs/z1/amst-cl01/output',
                          useroutput_mount='/ifs/z1/amst-cl01/useroutput',
                          raw_share='/raw/share',
                          perm_share='/perm/share',
                          resim_share='/resim/share',
                          output_share='/output/share',
                          useroutput_share='/useroutput/share',
                          nfs_host='cluster-1',
                          smb_host='cluster-smb-1')

        self.client.clusters.create(cluster)
        self.client.sync_cluster_config()

    def tearDown(self):
        super(BaseTestCase, self).tearDown()
