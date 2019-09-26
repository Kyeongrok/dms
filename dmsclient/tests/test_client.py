import datetime
import time
import unittest

from dmsclient.client import DMSClient
from dmsclient.controllers.clusters import ClusterController
from dmsclient.controllers.drives import DriveController
from dmsclient.controllers.readers import ReaderController
from dmsclient.controllers.segments import SegmentController


class DMSClientTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(DMSClientTestCase, self).__init__(*args, **kwargs)
        self.drive_id_1 = "drive_id-%s" % int(time.time())
        self.drive_id_2 = self.drive_id_1 + '_2'

    def test_verify_controllers(self):
        c = DMSClient(
            es_endpoint='http://endpoint',
            es_user='someone',
            es_password='password',
            initial_sync=False,
            verify_templates=False,
            create_templates=False
        )

        controllers = [
            ('readers', ReaderController),
            ('clusters', ClusterController),
            ('drives', DriveController),
            ('segments', SegmentController)
        ]

        for controller in controllers:
            self.assertTrue(hasattr(c, controller[0]),
                            "Client does not have controller '%s'" % controller[0])
            self.assertIsInstance(getattr(c, controller[0]), controller[1])

    def test_verify_initial_syncd(self):
        c = DMSClient(
            es_endpoint='http://endpoint',
            es_user='someone',
            es_password='password',
            initial_sync=False,
            verify_templates=False,
            create_templates=False
        )

        self.assertEqual(c.last_sync, datetime.datetime.min)
