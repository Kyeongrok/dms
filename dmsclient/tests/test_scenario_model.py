from datetime import datetime
from unittest import TestCase

from dmsclient import factories
from dmsclient.models.scenario import Scenario
from dmsclient.models.scenariosegment import ScenarioSegment


class ScenarioModelTestCase(TestCase):
    ATTRIBUTES_TO_TEST = [
        'name',
        'user',
        'query',
        'sensor_versions',
        'scenario_segments',
        'created_at',
        'updated_at',
        'started_at',
        'ended_at',
        'state',
        'cpu_time',
        'output_path'
    ]

    def __init__(self, *args, **kwargs):
        super(ScenarioModelTestCase, self).__init__(*args, **kwargs)
        self.segments = []
        for i in range(10):
            segment = factories.SegmentFactory(tags=['abc', 'def'])
            self.segments.append(segment)

    def test_verify_attributes(self):

        s = factories.ScenarioFactory()

        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(s, attr))

    def test_verify_attributes_from_segment(self):
        s = Scenario.from_segments(name='abc',
                                   user='user1',
                                   query='',
                                   sensor_versions=[{'sensor': 'CAM', 'version': 'v1.2'}],
                                   segments=self.segments)

        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(s, attr), '%s is not an attribute' % attr)

    def test_constructor_from_drive(self):
        created_at = datetime(2017, 8, 23, 7, 30, 4)
        updated_at = datetime(2017, 8, 23, 7, 40, 23)
        started_at = datetime(2017, 8, 23, 7, 34, 10)
        ended_at = datetime(2017, 8, 23, 7, 55, 45)
        s = Scenario.from_segments(name='abc',
                                   user='user1',
                                   query="{'query': {'term': {'tags': 'abc'}}}",
                                   sensor_versions=[{'sensor': 'CAM', 'version': 'v1.2'}],
                                   segments=self.segments,
                                   state=Scenario.State.CREATED,
                                   created_at=created_at,
                                   updated_at=updated_at,
                                   started_at=started_at,
                                   ended_at=ended_at,
                                   cpu_time=1234,
                                   output_path='/output/path/')

        self.assertEqual(s.name, 'abc')
        self.assertEqual(s.user, 'user1')
        self.assertEqual(s.query, "{'query': {'term': {'tags': 'abc'}}}")
        self.assertEqual(s.sensor_versions, [{'sensor': 'CAM', 'version': 'v1.2'}])
        self.assertEqual(len(s.scenario_segments), len(self.segments))
        for ss in s.scenario_segments:
            self.assertIsInstance(ss, ScenarioSegment)
        self.assertEqual(s.created_at, created_at)
        self.assertEqual(s.updated_at, updated_at)
        self.assertEqual(s.started_at, started_at)
        self.assertEqual(s.ended_at, ended_at)
        self.assertEqual(s.state, Scenario.State.CREATED)
        self.assertEqual(s.cpu_time, 1234)
        self.assertEqual(s.output_path, '/output/path/')
