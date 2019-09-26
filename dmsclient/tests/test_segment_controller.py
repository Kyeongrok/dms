import datetime
import os
import time

from dmsclient import factories
from dmsclient.exceptions import DMSClientException, DMSDocumentNotFoundError, DMSConflictError
from dmsclient.models.segment import Segment
from tests import BaseTestCase


class SegmentControllerTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(SegmentControllerTestCase, self).__init__(*args, **kwargs)
        self.drive_1 = None
        self.drive_1 = factories.DriveFactory(car_id='21YD3',
                                              project_name='Z1',
                                              logged_at=datetime.datetime(2017, 8, 23, 7, 30, 4),
                                              extra_field_1='extra-field-1-value',
                                              extra_field_2='extra-field-2-value',
                                              extra_field_3='extra-field-3-value')
        self.segment_1_id = 'Z1_21YD3_CONT_20170823T073004-20170823T073454'

    def setUp(self):
        super(SegmentControllerTestCase, self).setUp()
        self.client.drives.index(self.drive_1)
        self.client.segments.create_from_drive(self.segment_1_id,
                                               sequence=1,
                                               drive=self.drive_1,
                                               tags=['raw', 'test', 'raining'],
                                               extra_field_1='extra-field-1-value',
                                               extra_field_2='extra-field-2-value',
                                               extra_field_3='extra-field-3-value'
                                               )

    def tearDown(self):
        super(SegmentControllerTestCase, self).tearDown()
        for drive_id in [self.drive_1.drive_id]:
            try:
                self.client.drives.delete(drive_id)
                self.client.segments.delete_by_drive_id(drive_id)
            except DMSClientException:
                pass

    def test_create_segment(self):
        extra_fields = {
            "field-%s_1" % int(time.time()): 'field-value-1',
            "field-%s_2" % int(time.time()): 'field-value-2',
            "field-%s_3" % int(time.time()): 'field-value-3'
        }
        self.client.segments.create_from_drive('Z1_21YD3_CONT_20170823T073455-20170823T073828',
                                               sequence=2,
                                               drive=self.drive_1,
                                               tags=['raw', 'test'],
                                               **extra_fields
                                               )
        s = self.client.segments.get('Z1_21YD3_CONT_20170823T073455-20170823T073828')
        self.assertEqual(s.segment_id, 'Z1_21YD3_CONT_20170823T073455-20170823T073828')
        self.assertEqual(s.sequence, 2)
        self.assertEqual(s.drive_id, self.drive_1.drive_id)
        self.assertEqual(s.project_name, self.drive_1.project_name)
        self.assertEqual(s.car_id, self.drive_1.car_id)
        self.assertEqual(s.state, Segment.State.CREATED)
        self.assertEqual(s.state, 'created')
        self.assertEqual(s.started_at, datetime.datetime(2017, 8, 23, 7, 34, 55, tzinfo=datetime.timezone.utc))
        self.assertEqual(s.ended_at, datetime.datetime(2017, 8, 23, 7, 38, 28, tzinfo=datetime.timezone.utc))
        self.assertEqual(s.perm_path, os.path.join('/ifs/z1/amst-cl01/perm/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.resim_path, os.path.join('/ifs/z1/amst-cl01/resim/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.output_path, os.path.join('/ifs/z1/amst-cl01/output/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.nfs_host, 'cluster-1')
        self.assertEqual(s.smb_host, 'cluster-smb-1')
        self.assertEqual(s.perm_export, os.path.join('/perm/export/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.resim_export, os.path.join('/resim/export/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.output_export, os.path.join('/output/export/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.perm_share, os.path.join('/perm/share/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.resim_share, os.path.join('/resim/share/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.output_share, os.path.join('/output/share/21YD3/201708/23T073004/0002'))
        self.assertEqual(s.tags, ['raw', 'test'])
        for field in extra_fields:
            self.assertIn(field, s.extra_fields)

    def test_create_segment_duplicate(self):
        with self.assertRaises(DMSConflictError) as error:
            self.client.segments.create_from_drive(self.segment_1_id,
                                                   sequence=1,
                                                   drive=self.drive_1)
        exception = error.exception
        self.assertEqual(409, exception.status_code)

    def test_find_segments_by_drive_id(self):
        segments = self.client.segments.find_by_drive_id(self.drive_1.drive_id)

        segments = list(segments)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].segment_id, self.segment_1_id)

    def test_find_by_tags(self):
        segments = self.client.segments.find_by_fields(tags='raw')

        segments = list(segments)
        self.assertGreaterEqual(len(segments), 1)
        self.assertIn('raw', segments[0].tags)

    def test_find_by_other_fields(self):
        segments = self.client.segments.find_by_fields(
            project_name=self.drive_1.project_name,
            state=Segment.State.CREATED)

        segments = list(segments)
        self.assertGreaterEqual(len(segments), 1)
        self.assertEqual(self.drive_1.project_name, segments[0].project_name)
        self.assertEqual(Segment.State.CREATED, segments[0].state)

    def test_delete_segment(self):
        self.client.segments.get(self.segment_1_id)

        self.client.segments.delete(self.segment_1_id)

        f = self.client.segments.get
        self.assertRaises(DMSDocumentNotFoundError, f, self.segment_1_id)

    def test_delete_segment_no_match(self):
        f = self.client.segments.delete
        self.assertRaises(DMSDocumentNotFoundError, f, 'FAKE_ID_123')

    def test_delete_segment_by_drive_id(self):
        r = list(self.client.segments.find_by_drive_id(self.drive_1.drive_id))
        self.assertEqual(len(r), 1)

        deleted = self.client.segments.delete_by_drive_id(self.drive_1.drive_id)
        self.assertEqual(deleted, 1)

        r = list(self.client.segments.find_by_drive_id(self.drive_1.drive_id))
        self.assertEqual(len(r), 0)

    def test_delete_segment_by_drive_id_no_match(self):
        deleted = self.client.segments.delete_by_drive_id('FAKE_DRIVE_ID_123')
        self.assertEqual(deleted, 0)

    def test_add_tags(self):
        tags_to_add = ['tag-1', 'tag-2']

        original_tags = self.client.segments.get_tags(self.segment_1_id)
        for tag in tags_to_add:
            self.assertNotIn(tag, original_tags)

        self.client.segments.add_tags(self.segment_1_id, tags_to_add)
        updated_tags = self.client.segments.get_tags(self.segment_1_id)

        self.assertCountEqual(updated_tags, original_tags + tags_to_add)

    def test_remove_tags(self):
        tags_to_remove = ['test', 'raining']

        original_tags = self.client.segments.get_tags(self.segment_1_id)
        for tag in tags_to_remove:
            self.assertIn(tag, original_tags)

        self.client.segments.remove_tags(self.segment_1_id, tags_to_remove)
        updated_tags = self.client.segments.get_tags(self.segment_1_id)

        for tag in tags_to_remove:
            self.assertNotIn(tag, updated_tags)

    def test_set_state(self):
        desired_state = Segment.State.STARTED
        initial_state = self.client.segments.get_state(self.segment_1_id)
        self.assertNotEqual(initial_state, desired_state)

        self.client.segments.set_state(self.segment_1_id, desired_state)

        final_state = self.client.segments.get_state(self.segment_1_id)
        self.assertEqual(final_state, desired_state)

    def test_set_invalid_state(self):
        f = self.client.segments.set_state
        self.assertRaises(ValueError, f, self.segment_1_id, 'fake-state')

    def test_set_state_nonexistent_segment(self):
        f = self.client.segments.set_state
        self.assertRaises(DMSDocumentNotFoundError, f, 'FAKE_ID_123', Segment.State.CREATED)

    def test_get_state(self):
        state = self.client.segments.get_state(self.segment_1_id)
        self.assertEqual(state, Segment.State.CREATED)

    def test_get_state_nonexistent_segment(self):
        f = self.client.segments.get_state
        self.assertRaises(DMSDocumentNotFoundError, f, 'FAKE_ID_123')

    def test_set_extra_fields(self):
        extra_fields = {
            "field_%s_1" % int(time.time()): 'field-value-1',
            "field_%s_2" % int(time.time()): 'field-value-2',
            "field_%s_3" % int(time.time()): 'field-value-3'
        }
        self.client.segments.set_fields(self.segment_1_id, **extra_fields)

        segment = self.client.segments.get(self.segment_1_id)

        for field in extra_fields:
            self.assertIn(field, segment.extra_fields)

    def test_set_fields_protected(self):
        fields = {
            "car_id": 'field-value-1'
        }
        with self.assertRaises(ValueError) as error:
            self.client.segments.set_fields(self.segment_1_id, **fields)
        exception = error.exception
        self.assertIn("'car_id' is a protected field of Segment.", str(exception))

    def test_remove_extra_field(self):
        field_to_remove = 'extra_field_1'
        segment = self.client.segments.get(self.segment_1_id)
        self.assertIn(field_to_remove, segment.extra_fields)

        self.client.segments.remove_field(self.segment_1_id, field_to_remove)

        segment = self.client.segments.get(self.segment_1_id)
        self.assertNotIn(field_to_remove, segment.extra_fields)

    def test_remove_extra_field_nonexistent_segment(self):
        f = self.client.segments.remove_field
        self.assertRaises(DMSDocumentNotFoundError, f, 'FAKE_ID_123', 'field_x')

    def test_remove_field_protected(self):
        field = 'car_id'
        with self.assertRaises(ValueError) as error:
            self.client.segments.remove_field(self.segment_1_id, field)
        exception = error.exception
        self.assertIn("'car_id' is a protected field of Segment.", str(exception))
