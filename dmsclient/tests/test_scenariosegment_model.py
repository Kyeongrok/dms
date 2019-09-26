from unittest import TestCase

from dmsclient.models.scenariosegment import ScenarioSegment


class ScenarioSegmentModelTestCase(TestCase):
    ATTRIBUTES_TO_TEST = [
        'scenario_id',
        'segment_id',
        'state'
    ]

    def __init__(self, *args, **kwargs):
        super(ScenarioSegmentModelTestCase, self).__init__(*args, **kwargs)
        self.ss = ScenarioSegment(scenario_id='sc-123',
                                  segment_id='sg-456',
                                  state=ScenarioSegment.State.FAILED)

    def test_verify_attributes(self):
        for attr in self.ATTRIBUTES_TO_TEST:
            self.assertTrue(hasattr(self.ss, attr))

    def test_constructor(self):
        self.assertEqual(self.ss.scenario_id, 'sc-123')
        self.assertEqual(self.ss.segment_id, 'sg-456')
        self.assertEqual(self.ss.state, ScenarioSegment.State.FAILED)
