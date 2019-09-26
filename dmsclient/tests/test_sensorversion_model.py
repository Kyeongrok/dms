from unittest import TestCase

from dmsclient import factories
from dmsclient.models.sensorversion import SensorVersion
from tests.test_sensor_model import SensorModelTestCase


class SensorVersionModelTestCase(TestCase):
    ATTRIBUTES_TO_TEST = SensorModelTestCase.ATTRIBUTES_TO_TEST + [
        'sensorversion_id',
        'version'
    ]

    def __init__(self, *args, **kwargs):
        super(SensorVersionModelTestCase, self).__init__(*args, **kwargs)

    def test_verify_attributes(self):

        s = factories.SensorVersionFactory()

        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(s, attr), '%s is not an attribute' % attr)

    def test_verify_attributes_from_sensor(self):
        sensor = factories.SensorFactory()
        s = SensorVersion.from_sensor(sensor=sensor,
                                      version='0145')

        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(s, attr), '%s is not an attribute' % attr)

    def test_constructor_from_sensor(self):
        sensor = factories.SensorFactory(sensor_type='LDR',
                                         tags=['raw', 'test'])

        sv = SensorVersion.from_sensor(sensor=sensor,
                                       version='0145')

        self.assertEqual(sv.sensorversion_id, sensor.sensor_id + '_0145')
        self.assertEqual(sv.version, '0145')
        self.assertEqual(sv.sensor_id, sensor.segment_id + '_LDR')
        self.assertEqual(sv.segment_id, sensor.segment_id)
        self.assertEqual(sv.sensor_type, 'LDR')
        self.assertEqual(sv.state, SensorVersion.State.CREATED)
        self.assertEqual(sv.perm_path, sensor.perm_path)
        self.assertEqual(sv.resim_path, sensor.resim_path)
        self.assertEqual(sv.output_path, sensor.output_path)
        self.assertEqual(sv.tags, sensor.tags)
