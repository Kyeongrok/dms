import os
import time

from dmsclient import factories
from dmsclient.exceptions import DMSClientException, DMSDocumentNotFoundError, DMSConflictError
from dmsclient.models.sensor import Sensor
from dmsclient.models.sensorversion import SensorVersion
from tests import BaseTestCase


class SensorControllerTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(SensorControllerTestCase, self).__init__(*args, **kwargs)
        self.sensor_1 = factories.SensorFactory(tags=['raw', 'test', 'raining'],
                                                sensor_type='FLC',
                                                state='created',
                                                extra_field_1='extra-field-1-value')
        self.sensor_2 = factories.SensorFactory(sensor_type='FLC',
                                                tags=['raw', 'test'],
                                                extra_field_1='extra-field-1-value',
                                                extra_field_2='extra-field-2-value',
                                                extra_field_3='extra-field-3-value'
                                                )

    def setUp(self):
        super(SensorControllerTestCase, self).setUp()
        self.client.sensors.create(self.sensor_1)

    def tearDown(self):
        super(SensorControllerTestCase, self).tearDown()
        for sensor_id in [self.sensor_1.sensor_id,
                          self.sensor_2.sensor_id]:
            try:
                self.client.sensors.delete(sensor_id)
            except DMSClientException:
                pass

    def test_create_sensor(self):

        self.client.sensors.create(self.sensor_2)

        s = self.client.sensors.get(self.sensor_2.sensor_id)

        self.assertEqual(s.sensor_id, self.sensor_2.segment_id + '_FLC')
        self.assertEqual(s.segment_id, self.sensor_2.segment_id)
        self.assertEqual(s.sensor_type, 'FLC')
        self.assertEqual(s.state, Sensor.State.CREATED)
        self.assertEqual(s.perm_path, os.path.join('/perm/path',
                                                   self.sensor_2.segment_id))
        self.assertEqual(s.resim_path, os.path.join('/resim/path',
                                                    self.sensor_2.segment_id))
        self.assertEqual(s.output_path, os.path.join('/output/path',
                                                     self.sensor_2.segment_id))
        self.assertEqual(s.tags, ['raw', 'test'])
        self.assertEqual(s.extra_fields['extra_field_1'], 'extra-field-1-value')
        self.assertEqual(s.extra_fields['extra_field_2'], 'extra-field-2-value')
        self.assertEqual(s.extra_fields['extra_field_3'], 'extra-field-3-value')

    def test_create_segment_duplicate(self):
        with self.assertRaises(DMSConflictError) as error:
            self.client.sensors.create(self.sensor_1)
        exception = error.exception
        self.assertEqual(409, exception.status_code)

    def test_create_sensor_from_segment(self):
        extra_fields = {
            "field-%s_1" % int(time.time()): 'field-value-1',
            "field-%s_2" % int(time.time()): 'field-value-2',
            "field-%s_3" % int(time.time()): 'field-value-3'
        }
        segment = factories.SegmentFactory()
        self.client.sensors.create_from_segment(segment=segment,
                                                sensor_type='FSRL',
                                                **extra_fields)

        s = self.client.sensors.get(segment.segment_id + '_FSRL')

        self.assertEqual(s.sensor_id, segment.segment_id + '_FSRL')
        self.assertEqual(s.segment_id, segment.segment_id)
        self.assertEqual(s.sensor_type, 'FSRL')
        self.assertEqual(s.state, Sensor.State.CREATED)
        self.assertEqual(s.state, 'created')
        self.assertEqual(s.perm_path, segment.perm_path)
        self.assertEqual(s.resim_path, segment.resim_path)
        self.assertEqual(s.output_path, segment.output_path)
        self.assertEqual(s.tags, segment.tags)
        for field in extra_fields:
            self.assertIn(field, s.extra_fields)

    def test_find_sensors_by_segment_id(self):
        sensors = self.client.sensors.find_by_segment_id(self.sensor_1.segment_id)

        sensors = list(sensors)
        self.assertEqual(len(sensors), 1)
        self.assertEqual(sensors[0], self.sensor_1)

    def test_find_by_tags(self):
        sensors = self.client.sensors.find_by_fields(tags='raw')

        sensors = list(sensors)
        self.assertGreaterEqual(len(sensors), 1)
        self.assertIn('raw', sensors[0].tags)

    def test_find_by_other_fields(self):
        sensors = self.client.sensors.find_by_fields(sensor_type='FSRL', state='created')

        sensors = list(sensors)
        self.assertGreaterEqual(len(sensors), 1)
        self.assertEqual(Sensor.State.CREATED, sensors[0].state)
        self.assertEqual('FSRL', sensors[0].sensor_type)

    def test_delete_sensor(self):
        self.client.sensors.get(self.sensor_1.sensor_id)

        self.client.sensors.delete(self.sensor_1.sensor_id)

        f = self.client.sensors.get
        self.assertRaises(DMSDocumentNotFoundError, f, self.sensor_1.sensor_id)

    def test_delete_sensors_by_segment_id(self):
        sensors = self.client.sensors.find_by_segment_id(self.sensor_1.segment_id)
        self.assertGreater(len(list(sensors)), 0)

        self.client.sensors.delete_by_segment_id(self.sensor_1.segment_id)

        sensors = self.client.sensors.find_by_segment_id(self.sensor_1.segment_id)
        self.assertEqual(len(list(sensors)), 0)

    def test_add_tags(self):
        tags_to_add = ['tag-1', 'tag-2']

        original_tags = self.client.sensors.get_tags(self.sensor_1.sensor_id)
        for tag in tags_to_add:
            self.assertNotIn(tag, original_tags)

        self.client.sensors.add_tags(self.sensor_1.sensor_id, tags_to_add)
        updated_tags = self.client.sensors.get_tags(self.sensor_1.sensor_id)

        self.assertCountEqual(updated_tags, original_tags + tags_to_add)

    def test_remove_tags(self):
        tags_to_remove = ['test', 'raining']

        original_tags = self.client.sensors.get_tags(self.sensor_1.sensor_id)
        for tag in tags_to_remove:
            self.assertIn(tag, original_tags)

        self.client.sensors.remove_tags(self.sensor_1.sensor_id, tags_to_remove)
        updated_tags = self.client.sensors.get_tags(self.sensor_1.sensor_id)

        for tag in tags_to_remove:
            self.assertNotIn(tag, updated_tags)

    def test_set_state(self):
        desired_state = Sensor.State.SHIPPED
        initial_state = self.client.sensors.get_state(self.sensor_1.sensor_id)
        self.assertNotEqual(initial_state, desired_state)

        self.client.sensors.set_state(self.sensor_1.sensor_id, desired_state)

        final_state = self.client.sensors.get_state(self.sensor_1.sensor_id)
        self.assertEqual(final_state, desired_state)

    def test_set_invalid_state(self):
        f = self.client.sensors.set_state
        self.assertRaises(ValueError, f, self.sensor_1.sensor_id, 'fake-state')

    def test_set_state_nonexistent_sensor(self):
        f = self.client.sensors.set_state
        self.assertRaises(DMSDocumentNotFoundError, f, 'FAKE_ID_123', Sensor.State.CREATED)

    def test_get_state(self):
        state = self.client.sensors.get_state(self.sensor_1.sensor_id)
        self.assertEqual(state, Sensor.State.CREATED)

    def test_get_state_nonexistent_sensor(self):
        f = self.client.sensors.get_state
        self.assertRaises(DMSDocumentNotFoundError, f, 'FAKE_ID_123')

    def test_set_extra_fields(self):
        extra_fields = {
            "field_%s_1" % int(time.time()): 'field-value-1',
            "field_%s_2" % int(time.time()): 'field-value-2',
            "field_%s_3" % int(time.time()): 'field-value-3'
        }
        self.client.sensors.set_fields(self.sensor_1.sensor_id, **extra_fields)

        sensor = self.client.sensors.get(self.sensor_1.sensor_id)

        for field in extra_fields:
            self.assertIn(field, sensor.extra_fields)

    def test_set_fields_protected(self):
        fields = {
            "sensor_type": 'field-value-1'
        }
        with self.assertRaises(ValueError) as error:
            self.client.sensors.set_fields(self.sensor_1.sensor_id, **fields)
        exception = error.exception
        self.assertIn("'sensor_type' is a protected field of Sensor.", str(exception))

    def test_remove_extra_field(self):
        field_to_remove = 'extra_field_1'
        segment = self.client.sensors.get(self.sensor_1.sensor_id)
        self.assertIn(field_to_remove, segment.extra_fields)

        self.client.sensors.remove_field(self.sensor_1.sensor_id, field_to_remove)

        segment = self.client.sensors.get(self.sensor_1.sensor_id)
        self.assertNotIn(field_to_remove, segment.extra_fields)

    def test_remove_field_protected(self):
        field = 'sensor_type'
        with self.assertRaises(ValueError) as error:
            self.client.sensors.remove_field(self.sensor_1.sensor_id, field)
        exception = error.exception
        self.assertIn("'sensor_type' is a protected field of Sensor.", str(exception))

    def test_get_versions(self):
        self.client.sensors.create_version(self.sensor_1, '0011')
        self.client.sensors.create_version(self.sensor_1, '0012')
        self.client.sensors.create_version(self.sensor_1, '0013')

        versions = self.client.sensors.get_versions(self.sensor_1.sensor_id)
        self.assertEqual(len(versions), 3)
        for version in versions:
            self.assertIn(version.version, ['0011', '0012', '0013'])

    def test_get_versions_no_match(self):
        versions = self.client.sensors.get_versions(self.sensor_1.sensor_id)
        self.assertEqual(len(versions), 0)

    def test_get_version(self):
        self.client.sensors.create_version(self.sensor_1, '0019')
        sensorversion = self.client.sensors.get_version(self.sensor_1.sensor_id, '0019')
        self.assertEqual(sensorversion.version, '0019')

    def test_get_version_unknown(self):
        self.client.sensors.create_version(self.sensor_1, '0019')
        sensorversion = self.client.sensors.get_version(self.sensor_1.sensor_id, '0019')
        self.assertEqual(sensorversion.version, '0019')

    def test_get_version_no_match(self):
        f = self.client.sensors.get_version
        self.assertRaises(DMSDocumentNotFoundError, f, self.sensor_1.sensor_id, '0056')

    def test_create_version_from_filename(self):
        f = self.client.sensors.get_version
        self.assertRaises(DMSDocumentNotFoundError, f, self.sensor_1.sensor_id, '0023')

        filename = self.sensor_1.sensor_id + '_0023.dat'
        self.client.sensors.create_version_from_filename(filename)

        sensorversion = self.client.sensors.get_version(self.sensor_1.sensor_id, '0023')
        self.assertEqual(sensorversion.version, '0023')

    def test_create_existing_version(self):
        self.client.sensors.create_version(self.sensor_1, '0011')

        with self.assertRaises(DMSClientException) as error:
            self.client.sensors.create_version(self.sensor_1, '0011')
        exception = error.exception
        self.assertEqual(409, exception.status_code)
        self.assertIn('conflict', exception.message)

    def test_update_version(self):
        self.client.sensors.create_version(self.sensor_1, '0011')
        self.client.sensors.update_version(self.sensor_1.sensor_id, '0011',
                                           state=SensorVersion.State.REQUESTED,
                                           extra_field_1='value-1')

        sensorversion = self.client.sensors.get_version(self.sensor_1.sensor_id, '0011')
        self.assertEqual(sensorversion.state, SensorVersion.State.REQUESTED)
        self.assertEqual(sensorversion.extra_fields['extra_field_1'], 'value-1')

    def test_delete_version(self):
        self.client.sensors.create_version(self.sensor_1, '0011')
        versions = self.client.sensors.get_versions(self.sensor_1.sensor_id)
        self.assertEqual(len(versions), 1)

        self.client.sensors.delete_version(self.sensor_1.sensor_id, '0011')

        versions = self.client.sensors.get_versions(self.sensor_1.sensor_id)
        self.assertEqual(len(versions), 0)

    def test_delete_nonexistent_version(self):
        f = self.client.sensors.delete_version
        self.assertRaises(DMSDocumentNotFoundError, f, self.sensor_1.sensor_id, '0011')
