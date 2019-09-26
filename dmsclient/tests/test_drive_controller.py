import datetime
import time

from dateutil.tz import tzutc

from dmsclient import factories
from dmsclient.models.drive import Drive

from dmsclient.exceptions import DMSClientException, DMSConflictError, DMSDocumentNotFoundError
from tests import BaseTestCase


class DriveControllerTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(DriveControllerTestCase, self).__init__(*args, **kwargs)
        self.drive_1 = factories.DriveFactory(state='created',
                                              tags=['raw', 'test', 'raining'],
                                              extra_field_1='extra-field-1-value',
                                              extra_field_2='extra-field-2-value',
                                              extra_field_3='extra-field-3-value')
        self.drive_id_2 = 'Z1_MLB090_CONT_20170823T073000'

    def setUp(self):
        super(DriveControllerTestCase, self).setUp()
        self.client.drives.index(self.drive_1)

    def tearDown(self):
        super(DriveControllerTestCase, self).tearDown()
        for drive_id in [self.drive_1.drive_id,
                         self.drive_id_2]:
            try:
                self.client.drives.delete(drive_id)
            except DMSClientException:
                pass

    def test_index_drive(self):
        d = factories.DriveFactory(drive_id=self.drive_id_2)
        self.client.drives.index(d)
        response = self.client.drives.get(d.drive_id)
        self.assertEqual(response, d)

    def test_create_drive_from_ingest(self):
        drive1 = self.client.drives.create_from_ingest(dir_name=self.drive_id_2,
                                                       source_path='/source/path',
                                                       ingest_station='ingest-host-123',
                                                       size=325456,
                                                       file_count=239,
                                                       ingest_duration=738)
        drive2 = self.client.drives.get(self.drive_id_2)

        smb_share = '/raw/share/MLB090/201708/23T073000/Z1_MLB090_CONT_20170823T073000'
        self.assertEqual(drive1, drive2)
        self.assertEqual(drive2.project_name, 'Z1')
        self.assertEqual(drive2.car_id, 'MLB090')
        self.assertEqual(drive2.logged_at, datetime.datetime(2017, 8, 23, 7, 30, 0, tzinfo=tzutc()))
        self.assertEqual(drive2.drive_id, 'Z1_MLB090_CONT_20170823T073000')
        self.assertEqual(drive2.source_path, '/source/path')
        self.assertEqual(drive2.ingest_station, 'ingest-host-123')
        self.assertEqual(drive2.size, 325456)
        self.assertEqual(drive2.file_count, 239)
        self.assertEqual(drive2.ingest_duration, 738)
        self.assertEqual(drive2.nfs_host, 'cluster-1')
        self.assertEqual(drive2.smb_host, 'cluster-smb-1')
        self.assertEqual(drive2.smb_share, smb_share)

    def test_create_drive_duplicate(self):
        with self.assertRaises(DMSConflictError) as error:
            self.client.drives.create_from_ingest(dir_name=self.drive_1.drive_id,
                                                  source_path='/source/path',
                                                  ingest_station='ingest-host-123',
                                                  size=325456,
                                                  file_count=239,
                                                  ingest_duration=738)
        exception = error.exception
        self.assertEqual(409, exception.status_code)

    def test_index_drive_invalid_type(self):
        f = self.client.drives.index
        self.assertRaises(AssertionError, f, 'DRIVE-ID-123')

    def test_get_drive(self):
        drive = self.client.drives.get(self.drive_1.drive_id)
        self.assertIsInstance(drive, Drive)
        self.assertEqual(drive.drive_id, self.drive_1.drive_id)

    def test_get_drive_invalid_id(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.drives.get('FAKE_ID_123')
        exception = error.exception
        self.assertEqual(str(exception), "Could not find Drive with ID 'FAKE_ID_123'")

    def test_delete_drive(self):
        self.client.drives.delete(self.drive_1.drive_id)

        with self.assertRaises(DMSClientException) as error:
            self.client.drives.get(self.drive_1.drive_id)
        exception = error.exception

        self.assertEqual(404, exception.status_code)

    def test_delete_nonexistent_drive(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.drives.delete('FAKE_ID_123')
        exception = error.exception
        self.assertEqual(str(exception), "Could not find Drive with ID 'FAKE_ID_123'")

    def test_drive_set_state(self):
        desired_state = Drive.State.COPYING
        initial_state = self.client.drives.get_state(self.drive_1.drive_id)
        self.assertNotEqual(initial_state, desired_state)

        self.client.drives.set_state(self.drive_1.drive_id, desired_state)

        final_state = self.client.drives.get_state(self.drive_1.drive_id)
        self.assertEqual(final_state, desired_state)

    def test_drive_set_invalid_state(self):
        f = self.client.drives.set_state
        self.assertRaises(ValueError, f, self.drive_1.drive_id, 'fake-state')

    def test_drive_set_state_nonexistent_drive(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.drives.set_state('FAKE_ID_123', 'created')
        exception = error.exception
        self.assertEqual(str(exception), "Could not find Drive with ID 'FAKE_ID_123'")

    def test_drive_get_state(self):
        state = self.client.drives.get_state(self.drive_1.drive_id)
        self.assertEqual(state, Drive.State.CREATED)
        self.assertEqual(state, 'created')

    def test_drive_get_state_nonexistent_drive(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.drives.get_state('FAKE_ID_123')
        exception = error.exception
        self.assertEqual(str(exception), "Could not find Drive with ID 'FAKE_ID_123'")

    def test_add_tags_to_drive(self):
        tags_to_add = ['tag-1', 'tag-2']

        original_tags = self.client.drives.get_tags(self.drive_1.drive_id)
        for tag in tags_to_add:
            self.assertNotIn(tag, original_tags)

        self.client.drives.add_tags(self.drive_1.drive_id, tags_to_add)
        updated_tags = self.client.drives.get_tags(self.drive_1.drive_id)

        self.assertCountEqual(updated_tags, original_tags + tags_to_add)

    def test_add_tags_to_drive_invalid_type(self):
        f = self.client.drives.add_tags
        self.assertRaises(AssertionError, f, self.drive_1.drive_id, 'tag-123')

    def test_add_tags_to_nonexistent_drive(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.drives.add_tags('FAKE_ID_123', ['mytag'])
        exception = error.exception
        self.assertEqual(str(exception), "Could not find Drive with ID 'FAKE_ID_123'")

    def test_remove_tags_to_drive(self):
        tags_to_remove = ['test', 'raining']

        original_tags = self.client.drives.get_tags(self.drive_1.drive_id)
        for tag in tags_to_remove:
            self.assertIn(tag, original_tags)

        self.client.drives.remove_tags(self.drive_1.drive_id, tags_to_remove)
        updated_tags = self.client.drives.get_tags(self.drive_1.drive_id)

        for tag in tags_to_remove:
            self.assertNotIn(tag, updated_tags)

    def test_find_drive_by_query(self):
        extra_field = "extra_field_%s" % int(time.time())
        drive = factories.DriveFactory(drive_id=self.drive_id_2,
                                       **{extra_field: 'extra_value_1'})
        self.client.drives.index(drive)

        query = {
            'query': {
                'bool': {
                    'must': {
                        'match': {
                            extra_field: 'extra_value_1'
                        }
                    }
                }
            }
        }

        drives = self.client.drives.find_by_query(query)

        drives = list(drives)
        self.assertEqual(len(drives), 1)
        self.assertEqual(drives[0], drive)

    def test_find_drive_by_fields(self):
        extra_field = "extra_field_%s" % int(time.time())
        drive = factories.DriveFactory(drive_id=self.drive_id_2,
                                       **{extra_field: 'extra_value_1'})
        self.client.drives.index(drive)

        drives = self.client.drives.find_by_fields(**{extra_field: 'extra_value_1'})

        drives = list(drives)
        self.assertEqual(len(drives), 1)
        self.assertEqual(drive, drives[0])

    def test_find_drive_by_tag(self):

        drives = self.client.drives.find_by_fields(tags='raw')

        drives = list(drives)
        self.assertGreaterEqual(len(drives), 1)
        self.assertIn('raw', drives[0].tags)

    def test_find_drive_no_hits(self):
        drives = self.client.drives.find_by_fields(tags='FAKE_TAG_123')

        drives = list(drives)
        self.assertEqual(len(drives), 0)

    def test_drive_set_extra_fields(self):
        extra_fields = {
            "field_%s_1" % int(time.time()): 'field-value-1',
            "field_%s_2" % int(time.time()): 'field-value-2',
            "field_%s_3" % int(time.time()): 'field-value-3'
        }
        self.client.drives.set_fields(self.drive_1.drive_id, **extra_fields)

        drive = self.client.drives.get(self.drive_1.drive_id)

        for field in extra_fields:
            self.assertIn(field, drive.extra_fields)

    def test_drive_set_fields_invalid(self):
        fields = {
            "car_id": 'field-value-1'
        }
        with self.assertRaises(ValueError) as error:
            self.client.drives.set_fields(self.drive_1.drive_id, **fields)
        exception = error.exception
        self.assertIn("'car_id' is a protected field of Drive.", str(exception))

    def test_drive_set_flc_state(self):
        desired_state = Drive.FLCState.READY
        d = self.client.drives.get(self.drive_1.drive_id)
        self.assertNotEqual(d.flc_state, desired_state)

        self.client.drives.set_fields(self.drive_1.drive_id, flc_state=Drive.FLCState.READY)

        d = self.client.drives.get(self.drive_1.drive_id)
        self.assertEqual(d.flc_state, desired_state)

    def test_drive_find_by_flc_state(self):
        l = list(self.client.drives.find_by_fields(flc_state=Drive.FLCState.READY))
        self.assertEqual(len(l), 0)

        self.client.drives.set_fields(self.drive_1.drive_id, flc_state=Drive.FLCState.READY)
        self.client.drives.create_from_ingest(dir_name=self.drive_id_2,
                                              source_path='/source/path',
                                              ingest_station='ingest-host-123',
                                              flc_state=Drive.FLCState.READY)

        l = list(self.client.drives.find_by_fields(flc_state=Drive.FLCState.READY))
        self.assertEqual(len(l), 2)
