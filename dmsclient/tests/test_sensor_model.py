from unittest import TestCase

from dmsclient import factories
from dmsclient.models.sensor import Sensor


class SensorModelTestCase(TestCase):
    ATTRIBUTES_TO_TEST = [
        'sensor_id',
        'segment_id',
        'sensor_type',
        'created_at',
        'updated_at',
        'state',
        'tags',
        'perm_path',
        'output_path',
        'resim_path',
        'extra_fields'
    ]

    def __init__(self, *args, **kwargs):
        super(SensorModelTestCase, self).__init__(*args, **kwargs)
        self.segment_1 = factories.SegmentFactory()

    def test_verify_attributes(self):

        s = factories.SensorFactory()

        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(s, attr))

    def test_verify_attributes_from_segment(self):
        s = Sensor.from_segment(segment=self.segment_1,
                                sensor_type='FSRL')

        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(s, attr), '%s is not an attribute' % attr)

    def test_constructor_from_segment(self):
        s = Sensor.from_segment(segment=self.segment_1,
                                sensor_type='FSRL')

        self.assertEqual(s.sensor_id, self.segment_1.segment_id + '_' + 'FSRL')
        self.assertEqual(s.segment_id, self.segment_1.segment_id)
        self.assertEqual(s.sensor_type, 'FSRL')
        self.assertEqual(s.state, Sensor.State.CREATED)
        self.assertEqual(s.perm_path, self.segment_1.perm_path)
        self.assertEqual(s.resim_path, self.segment_1.resim_path)
        self.assertEqual(s.output_path, self.segment_1.output_path)
