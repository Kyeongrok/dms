from datetime import datetime, timezone
from unittest import TestCase

from dmsclient import factories
from dmsclient.exceptions import DMSClientException
from dmsclient.models.segment import Segment


class SegmentModelTestCase(TestCase):
    ATTRIBUTES_TO_TEST = [
        'segment_id',
        'drive_id',
        'project_name',
        'car_id',
        'cluster_id',
        'started_at',
        'ended_at',
        'created_at',
        'updated_at',
        'state',
        'tags',
        'nfs_host',
        'smb_host',
        'output_export',
        'perm_export',
        'resim_export',
        'output_share',
        'perm_share',
        'resim_share',
        'perm_path',
        'output_path',
        'resim_path',
        'extra_fields'
    ]

    def __init__(self, *args, **kwargs):
        super(SegmentModelTestCase, self).__init__(*args, **kwargs)
        self.cluster_1 = factories.ClusterFactory()
        self.drive_1 = factories.DriveFactory(project_name='Z1',
                                              car_id='21YD3',
                                              logged_at=datetime(2017, 8, 23, 7, 30, 4))

    def test_verify_attributes(self):

        s = factories.SegmentFactory()

        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(s, attr))

    def test_verify_attributes_from_drive(self):
        s = Segment.from_drive(segment_id='Z1_21YD3_CONT_20171222T121729-20171222T121829',
                               sequence=1,
                               drive=self.drive_1,
                               cluster=self.cluster_1)

        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(s, attr), '%s is not an attribute' % attr)

    def test_constructor_from_drive(self):
        s = Segment.from_drive(segment_id='Z1_21YD3_CONT_20170823T073004-20170823T073520',
                               sequence=1,
                               drive=self.drive_1,
                               cluster=self.cluster_1)

        self.assertEqual(s.segment_id, 'Z1_21YD3_CONT_20170823T073004-20170823T073520')
        self.assertEqual(s.sequence, 1)
        self.assertEqual(s.drive_id, self.drive_1.drive_id)
        self.assertEqual(s.project_name, self.drive_1.project_name)
        self.assertEqual(s.car_id, self.drive_1.car_id)
        self.assertEqual(s.state, Segment.State.CREATED)
        self.assertEqual(s.started_at, datetime(2017, 8, 23, 7, 30, 4, tzinfo=timezone.utc))
        self.assertEqual(s.ended_at, datetime(2017, 8, 23, 7, 35, 20, tzinfo=timezone.utc))
        self.assertEqual(s.perm_path, '/ifs/z1/amst-cl01/perm/21YD3/201708/23T073004/0001')
        self.assertEqual(s.resim_path, '/ifs/z1/amst-cl01/resim/21YD3/201708/23T073004/0001')
        self.assertEqual(s.output_path, '/ifs/z1/amst-cl01/output/21YD3/201708/23T073004/0001')
        self.assertEqual(s.perm_export, '/perm/export/21YD3/201708/23T073004/0001')
        self.assertEqual(s.resim_export, '/resim/export/21YD3/201708/23T073004/0001')
        self.assertEqual(s.output_export, '/output/export/21YD3/201708/23T073004/0001')
        self.assertEqual(s.perm_share, '/perm/share/21YD3/201708/23T073004/0001')
        self.assertEqual(s.resim_share, '/resim/share/21YD3/201708/23T073004/0001')
        self.assertEqual(s.output_share, '/output/share/21YD3/201708/23T073004/0001')
        self.assertEqual(s.nfs_host, 'cluster-1')
        self.assertEqual(s.smb_host, 'cluster-smb-1')

    def test_constructor_from_drive_mismatch_car_id(self):
        with self.assertRaises(DMSClientException) as error:
            Segment.from_drive(segment_id='Z1_21YD9_CONT_20170823T073004-20171222T121829',
                               sequence=1,
                               drive=self.drive_1,
                               cluster=self.cluster_1)
        exception = error.exception
        self.assertEqual("car_id mismatch between drive and segment [21YD9!=21YD3]", str(exception))

    def test_constructor_from_drive_mismatch_project_name(self):
        with self.assertRaises(DMSClientException) as error:
            Segment.from_drive(segment_id='Z2_21YD3_CONT_20170823T073004-20171222T121829',
                               sequence=1,
                               drive=self.drive_1,
                               cluster=self.cluster_1)
        exception = error.exception
        self.assertEqual("project_name mismatch between drive and segment [Z2!=Z1]", str(exception))

    def test_constructor_from_drive_invalid_segment_id(self):
        with self.assertRaises(DMSClientException) as error:
            Segment.from_drive(segment_id='Z1_21YD3_CONT_20170823T073004-0004',
                               sequence=1,
                               drive=self.drive_1,
                               cluster=self.cluster_1)
        exception = error.exception
        self.assertEqual("Could not parse segment_id 'Z1_21YD3_CONT_20170823T073004-0004'", str(exception))
