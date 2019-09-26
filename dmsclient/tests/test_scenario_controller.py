from datetime import datetime

from dmsclient import factories
from dmsclient.exceptions import DMSClientException, DMSDocumentNotFoundError, DMSConflictError
from dmsclient.models.scenario import Scenario
from dmsclient.utils import build_scenario_id as _
from tests import BaseTestCase


class ScenarioControllerTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(ScenarioControllerTestCase, self).__init__(*args, **kwargs)
        self.scenario_1 = factories.ScenarioFactory(name='scenario-1234',
                                                    user='user-1234',
                                                    state=Scenario.State.COMPLETED)
        self.scenario_2 = factories.ScenarioFactory()

    def setUp(self):
        super(ScenarioControllerTestCase, self).setUp()
        self.client.scenarios.create(self.scenario_1)

    def tearDown(self):
        super(ScenarioControllerTestCase, self).tearDown()
        self.client.segments.delete_by_drive_id('TEST-DRIVE-123')
        for scenario in [self.scenario_1,
                         self.scenario_2]:
            try:
                self.client.scenarios.delete(_(scenario.name, scenario.user))
                pass
            except DMSClientException:
                pass

    def test_create_and_get_scenario(self):
        self.client.scenarios.create(self.scenario_2)
        s = self.client.scenarios.get(_(self.scenario_2.name, self.scenario_2.user))
        self.assertEqual(s, self.scenario_2)

    def test_create_scenario_duplicate(self):
        with self.assertRaises(DMSConflictError) as error:
            self.client.scenarios.create(self.scenario_1)
        exception = error.exception
        self.assertEqual(409, exception.status_code)

    def test_get_scenario_by_name_user(self):
        s = self.client.scenarios.get(_(self.scenario_1.name, self.scenario_1.user))
        self.assertEqual(s, self.scenario_1)

    def test_delete_scenario(self):
        self.client.scenarios.get(_(self.scenario_1.name, self.scenario_1.user))
        self.client.scenarios.delete(_(self.scenario_1.name, self.scenario_1.user))

        with self.assertRaises(DMSClientException) as error:
            self.client.scenarios.get(_(self.scenario_1.name, self.scenario_1.user))
        exception = error.exception

        self.assertEqual(404, exception.status_code)

    def test_create_scenario_from_segments(self):
        for i in range(20):
            segment = factories.SegmentFactory(tags=['abcdef'], drive_id='TEST-DRIVE-123')
            self.client.segments.create(segment)

        query = {
            'query': {
                'term': {'tags': 'abcdef'}
            }
        }

        segments = self.client.segments.find_by_query(query)
        scenario = Scenario.from_segments(name=self.scenario_2.name,
                                          user=self.scenario_2.user,
                                          query=query,
                                          sensor_versions=[{'sensor': 'CAM', 'version': 'v1.2'}],
                                          segments=segments)
        self.client.scenarios.create(scenario)

        scenario_returned = self.client.scenarios.get(_(scenario.name, scenario.user))

        self.assertEqual(scenario, scenario_returned)
        self.assertEqual(len(scenario.scenario_segments), 20)

    def test_find_by_fields(self):
        results = [
            self.client.scenarios.find_by_fields(user='user-1234'),
            self.client.scenarios.find_by_fields(name='scenario-1234'),
            self.client.scenarios.find_by_fields(state='completed'),
            self.client.scenarios.find_by_fields(name='scenario-1234',
                                                 user='user-1234',
                                                 state='completed')
        ]

        for result in results:
            r = list(result)
            self.assertEqual(len(r), 1)
            self.assertEqual(r[0], self.scenario_1)

    def test_find_by_fields_no_match(self):
        scenarios = self.client.scenarios.find_by_fields(user='FAKE-USER-123')
        scenarios = list(scenarios)
        self.assertEqual(len(scenarios), 0)

    def test_set_state(self):
        desired_state = Scenario.State.FAILED
        initial_state = self.client.scenarios.get_state(_(self.scenario_1.name, self.scenario_1.user))
        self.assertNotEqual(initial_state, desired_state)

        self.client.scenarios.set_state(_(self.scenario_1.name, self.scenario_1.user), desired_state)

        final_state = self.client.scenarios.get_state(_(self.scenario_1.name, self.scenario_1.user))
        self.assertEqual(final_state, desired_state)

    def test_set_invalid_state(self):
        f = self.client.scenarios.set_state
        self.assertRaises(ValueError, f, _(self.scenario_1.name, self.scenario_1.user), 'fake-state')

    def test_set_state_nonexistent_segment(self):
        f = self.client.scenarios.set_state
        self.assertRaises(DMSDocumentNotFoundError, f, _('FAKE_NAME_123', 'FAKE_USER_123'), Scenario.State.CREATED)

    def test_get_state(self):
        state = self.client.scenarios.get_state(_(self.scenario_1.name, self.scenario_1.user))
        self.assertEqual(state, Scenario.State.COMPLETED)

    def test_get_state_nonexistent(self):
        f = self.client.scenarios.get_state
        self.assertRaises(DMSDocumentNotFoundError, f, _('FAKE_NAME_123', 'FAKE_USER_123'))

    def test_update_fields(self):
        self.client.scenarios.set_fields(_(self.scenario_1.name, self.scenario_1.user),
                                         cpu_time=8399456,
                                         query='{"query": ""}',
                                         started_at=datetime(2017, 8, 23, 7, 30, 0),
                                         ended_at=datetime(2017, 8, 23, 7, 30, 10)
                                         )
        scenario = self.client.scenarios.get(_(self.scenario_1.name, self.scenario_1.user))

        self.assertEqual(scenario.cpu_time, 8399456)
        self.assertEqual(scenario.query, '{"query": ""}')
        self.assertEqual(scenario.started_at, datetime(2017, 8, 23, 7, 30, 0))
        self.assertEqual(scenario.ended_at, datetime(2017, 8, 23, 7, 30, 10))

    def test_update_fields_protected(self):
        with self.assertRaises(ValueError) as error:
            self.client.scenarios.set_fields(_(self.scenario_1.name, self.scenario_1.user),
                                             created_at=datetime(2017, 8, 23, 7, 30, 0))
        exception = error.exception
        self.assertIn("'created_at' is a protected field of Scenario.", str(exception))
