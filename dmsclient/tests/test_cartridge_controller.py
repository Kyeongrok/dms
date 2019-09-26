from dmsclient import factories
from dmsclient.exceptions import DMSClientException, DMSDocumentNotFoundError
from dmsclient.models.reader import Reader
from dmsclient.models.cartridge import Cartridge
from tests import BaseTestCase


class CartridgeControllerTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(CartridgeControllerTestCase, self).__init__(*args, **kwargs)
        self.cartridge_1 = factories.CartridgeFactory(
                                                    device='/dev/md0',
                                                    ingest_station='ingest-station-1',
                                                    usage=10.5,
                                                    workflow_type=Cartridge.WorkflowType.INGESTION,
                                                    ingest_state=Reader.IngestState.IDLE
        )

        self.cartridge_2 = factories.CartridgeFactory()

    def setUp(self):
        super(CartridgeControllerTestCase, self).setUp()
        self.client.cartridges.create(self.cartridge_1)

    def tearDown(self):
        super(CartridgeControllerTestCase, self).tearDown()
        for cartridge_id in [self.cartridge_1.cartridge_id,
                             self.cartridge_2.cartridge_id]:
            try:
                self.client.cartridges.delete(cartridge_id)
            except DMSClientException:
                pass

    def test_create_cartridge(self):
        self.client.cartridges.create(self.cartridge_2)
        self.client.cartridges.get(self.cartridge_2.cartridge_id)

    def test_get_cartridge(self):
        r = self.client.cartridges.get(self.cartridge_1.cartridge_id)
        self.assertEqual(self.cartridge_1, r)

    def test_delete_cartridge(self):
        self.client.cartridges.delete(self.cartridge_1.cartridge_id)

        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.cartridges.get(self.cartridge_1.cartridge_id)
        exception = error.exception
        self.assertEqual(404, exception.status_code)

    def test_delete_nonexistent_cartridge(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.cartridges.delete('123-456-789')
        exception = error.exception
        self.assertEqual(404, exception.status_code)
        self.assertIn("Could not find Cartridge with ID '123-456-789'", str(exception))

    def test_set_workflow_type(self):
        desired_wf_type = Cartridge.WorkflowType.FLC_INGESTION
        initial_wf_type = self.client.cartridges.get(self.cartridge_1.cartridge_id).workflow_type
        self.assertNotEqual(initial_wf_type, desired_wf_type)

        self.client.cartridges.set_workflow_type(self.cartridge_1.cartridge_id, desired_wf_type)

        final_type = self.client.cartridges.get(self.cartridge_1.cartridge_id).workflow_type
        self.assertEqual(final_type, desired_wf_type)

    def test_set_ingest_state(self):
        desired_state = Reader.IngestState.PROCESSING
        initial_state = self.client.cartridges.get(self.cartridge_1.cartridge_id).ingest_state
        self.assertNotEqual(initial_state, desired_state)

        self.client.cartridges.set_ingest_state(self.cartridge_1.cartridge_id, desired_state)

        final_state = self.client.cartridges.get(self.cartridge_1.cartridge_id).ingest_state
        self.assertEqual(final_state, desired_state)

    def test_set_usage(self):
        desired_usage = 2.5
        initial_usage= self.client.cartridges.get(self.cartridge_1.cartridge_id).usage
        self.assertNotEqual(initial_usage, desired_usage)

        self.client.cartridges.set_usage(self.cartridge_1.cartridge_id, desired_usage)

        final_usage = self.client.cartridges.get(self.cartridge_1.cartridge_id).usage
        self.assertEqual(final_usage, desired_usage)

    # def test_find_by_fields_match(self):
        # cartridges = self.client.cartridges.find_by_fields(ingest_station='ingest-station-1')
        # cartridges = list(cartridges)
        # self.assertEqual(len(cartridges), 1)
        # self.assertEqual(cartridges[0].ingest_station, 'ingest-station-1')

        # cartridges = self.client.cartridges.find_by_fields(device='/dev/md0')
        # cartridges = list(cartridges)
        # self.assertEqual(len(cartridges), 1)
        # self.assertEqual(cartridges[0].device, '/dev/md0')

        # cartridges = self.client.cartridges.find_by_fields(workflow_type=Cartridge.WorkflowType.INGESTION)
        # cartridges = list(cartridges)
        # self.assertEqual(len(cartridges), 1)
        # self.assertEqual(cartridges[0].workflow_type, Cartridge.WorkflowType.INGESTION)

        # cartridges = self.client.cartridges.find_by_fields(ingest_state=Reader.IngestState.IDLE)
        # cartridges = list(cartridges)
        # self.assertEqual(len(cartridges), 1)
        # self.assertEqual(cartridges[0].ingest_state, Reader.IngestState.IDLE)

        # cartridges = self.client.cartridges.find_by_fields(
        #                                            device='/dev/md0',
        #                                            ingest_station='ingest-station-1',
        #                                            usage=10.5,
        #                                            workflow_type=Cartridge.WorkflowType.INGESTION,
        #                                            ingest_state=Reader.IngestState.IDLE)
        # cartridges = list(cartridges)
        # self.assertEqual(len(cartridges), 1)
        # self.assertEqual(cartridges[0].ingest_station, 'ingest-station-1')
        # self.assertEqual(cartridges[0].device, '/dev/md0')
        # self.assertEqual(cartridges[0].usage, 10.5)
        # self.assertEqual(cartridges[0].workflow_type, Cartridge.WorkflowType.INGESTION)
        # self.assertEqual(cartridges[0].workflow_type, 'CAR')
        # self.assertEqual(cartridges[0].ingest_state, 'idle')
        # self.assertEqual(cartridges[0].ingest_state, Reader.IngestState.IDLE)

    def test_find_by_fields_no_match(self):
        cartridges = self.client.cartridges.find_by_fields(ingest_staton='ingest-station-2')
        cartridges = list(cartridges)
        self.assertEqual(len(cartridges), 0)

        cartridges = self.client.cartridges.find_by_fields(device='/dev/md1')
        cartridges = list(cartridges)
        self.assertEqual(len(cartridges), 0)

        cartridges = self.client.cartridges.find_by_fields(workflow_type='USB')
        cartridges = list(cartridges)
        self.assertEqual(len(cartridges), 0)

        cartridges = self.client.cartridges.find_by_fields(ingest_state='processing')
        cartridges = list(cartridges)
        self.assertEqual(len(cartridges), 0)

        cartridges = self.client.cartridges.find_by_fields(
                                                    device='/dev/md0',
                                                    ingest_station='ingest-station-2',
                                                    usage=10.5,
                                                    workflow_type=Cartridge.WorkflowType.INGESTION,
                                                    ingest_state=Reader.IngestState.IDLE)

        cartridges = list(cartridges)
        self.assertEqual(len(cartridges), 0)
