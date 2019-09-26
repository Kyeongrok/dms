from datetime import datetime, timezone
from unittest import TestCase

from dmsclient import factories
from dmsclient.models.drive import Drive

from dmsclient.exceptions import DMSClientException


class DriveModelTestCase(TestCase):

    def __init__(self, *args, **kwargs):
        super(DriveModelTestCase, self).__init__(*args, **kwargs)
        self.cluster_1 = factories.ClusterFactory()

    def test_verify_attributes(self):
        d = Drive(
            drive_id='DRIVE_ID_1',
            car_id='CAR_ID_1',
            project_name='PROJECT_1',
            cluster_id='123',
            ingest_station='ingest-host-123',
            state=Drive.State.CREATED,
            flc_state=Drive.FLCState.NOT_READY,
            logged_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            nfs_host='nfs-host-1',
            smb_host='smb-host-1',
            smb_share='/ifs/z1/path1',
            source_path='/source/path',
            target_path='/target/path',
            tags=['raw', 'test'],
            size=325456,
            file_count=239,
            ingest_duration=783
        )

        for attr in Drive.PROTECTED_ATTRIBUTES:
            self.assertTrue(hasattr(d, attr))

    def test_verify_attributes_from_ingest(self):
        d = Drive.from_ingest(cluster=self.cluster_1,
                              dir_name='Z1_MLB090_CONT_20170823T073000',
                              source_path='/source/path',
                              ingest_station='ingest-host-123')

        for attr in Drive.PROTECTED_ATTRIBUTES:
            self.assertTrue(hasattr(d, attr))

    def test_verify_attributes_from_elasticsearch(self):
        # d = Drive.from_elasticsearch()
        #
        # for attr in self.DRIVE_ATTRIBUTES:
        #     self.assertTrue(hasattr(d, attr))
        self.skipTest('Not implemented yet')

    def test_invalid_folder_from_ingest(self):
        with self.assertRaises(DMSClientException) as error:
            Drive.from_ingest(cluster=self.cluster_1,
                              dir_name='INVALID_FOLDER_NAME',
                              source_path='/source/path',
                              ingest_station='ingest-host-123')
        exception = error.exception.message
        self.assertEqual("Could not parse directory name 'INVALID_FOLDER_NAME'", str(exception))

    def test_from_ingest(self):
        d = Drive.from_ingest(cluster=self.cluster_1,
                              dir_name='Z1_MLB090_CONT_20170823T073004',
                              source_path='/source/path',
                              ingest_station='ingest-host-123',
                              size=325456,
                              file_count=239,
                              ingest_duration=783)

        self.assertEqual(d.drive_id, 'Z1_MLB090_CONT_20170823T073004')
        self.assertEqual(d.car_id, 'MLB090')
        self.assertEqual(d.project_name, 'Z1')
        self.assertEqual(d.logged_at, datetime(
            year=2017,
            month=8,
            day=23,
            hour=7,
            minute=30,
            second=4,
            tzinfo=timezone.utc
        ))
        smb_share = '/raw/share/MLB090/201708/23T073004/Z1_MLB090_CONT_20170823T073004'
        self.assertEqual(d.updated_at.date(), datetime.utcnow().date())
        self.assertEqual(d.state, Drive.State.CREATED)
        self.assertEqual(d.flc_state, Drive.FLCState.NOT_READY)
        self.assertEqual(d.source_path, '/source/path')
        self.assertEqual(d.tags, [])
        self.assertEqual(d.ingest_station, 'ingest-host-123')
        self.assertEqual(d.nfs_host, 'cluster-1')
        self.assertEqual(d.smb_host, 'cluster-smb-1')
        self.assertEqual(d.smb_share, smb_share)
        self.assertEqual(d.size, 325456)
        self.assertEqual(d.file_count, 239)
        self.assertEqual(d.ingest_duration, 783)

    def test_from_ingest_old_format(self):
        d = Drive.from_ingest(cluster=self.cluster_1,
                              dir_name='Z1_MLB090__CONT_20170823T073004',
                              source_path='/source/path',
                              ingest_station='ingest-host-123',
                              size=325456,
                              file_count=239,
                              ingest_duration=783)

        self.assertEqual(d.drive_id, 'Z1_MLB090__CONT_20170823T073004')
        self.assertEqual(d.car_id, 'MLB090')
        self.assertEqual(d.project_name, 'Z1')
        self.assertEqual(d.logged_at, datetime(
            year=2017,
            month=8,
            day=23,
            hour=7,
            minute=30,
            second=4,
            tzinfo=timezone.utc
        ))
        smb_share = '/raw/share/MLB090/201708/23T073004/Z1_MLB090__CONT_20170823T073004'
        self.assertEqual(d.updated_at.date(), datetime.utcnow().date())
        self.assertEqual(d.state, Drive.State.CREATED)
        self.assertEqual(d.flc_state, Drive.FLCState.NOT_READY)
        self.assertEqual(d.source_path, '/source/path')
        self.assertEqual(d.tags, [])
        self.assertEqual(d.ingest_station, 'ingest-host-123')
        self.assertEqual(d.nfs_host, 'cluster-1')
        self.assertEqual(d.smb_host, 'cluster-smb-1')
        self.assertEqual(d.smb_share, smb_share)
        self.assertEqual(d.size, 325456)
        self.assertEqual(d.file_count, 239)
        self.assertEqual(d.ingest_duration, 783)
