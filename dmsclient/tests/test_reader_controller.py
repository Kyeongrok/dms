from dmsclient import factories
from dmsclient.exceptions import DMSClientException, DMSDocumentNotFoundError
from dmsclient.models.reader import Reader
from tests import BaseTestCase


class ReaderControllerTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(ReaderControllerTestCase, self).__init__(*args, **kwargs)
        self.reader_1 = factories.ReaderFactory(hostname='ingest-station-1',
                                                device='/dev/md0',
                                                status=Reader.Status.EMPTY,
                                                ingest_state=Reader.IngestState.IDLE)
        self.reader_2 = factories.ReaderFactory()

    def setUp(self):
        super(ReaderControllerTestCase, self).setUp()
        self.client.readers.create(self.reader_1)

    def tearDown(self):
        super(ReaderControllerTestCase, self).tearDown()
        for reader_id in [self.reader_1.reader_id,
                          self.reader_2.reader_id]:
            try:
                self.client.readers.delete(reader_id)
            except DMSClientException:
                pass

    def test_create_reader(self):
        self.client.readers.create(self.reader_2)
        self.client.readers.get(self.reader_2.reader_id)

    def test_get_reader(self):
        r = self.client.readers.get(self.reader_1.reader_id)
        self.assertEqual(self.reader_1, r)

    def test_delete_reader(self):
        self.client.readers.delete(self.reader_1.reader_id)

        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.readers.get(self.reader_1.reader_id)
        exception = error.exception
        self.assertEqual(404, exception.status_code)

    def test_delete_nonexistent_reader(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.readers.delete('FAKE_ID_123')
        exception = error.exception
        self.assertEqual(404, exception.status_code)
        self.assertIn("Could not find Reader with ID 'FAKE_ID_123'", str(exception))

    def test_set_status(self):
        desired_status = Reader.Status.ACTIVE
        initial_status = self.client.readers.get(self.reader_1.reader_id).status
        self.assertNotEqual(initial_status, desired_status)

        self.client.readers.set_status(self.reader_1.reader_id, desired_status)

        final_status = self.client.readers.get(self.reader_1.reader_id).status
        self.assertEqual(final_status, desired_status)

    def test_set_ingest_state(self):
        desired_state = Reader.IngestState.PROCESSING
        initial_state = self.client.readers.get(self.reader_1.reader_id).ingest_state
        self.assertNotEqual(initial_state, desired_state)

        self.client.readers.set_ingest_state(self.reader_1.reader_id, desired_state)

        final_state = self.client.readers.get(self.reader_1.reader_id).ingest_state
        self.assertEqual(final_state, desired_state)

    def test_set_message(self):
        desired_message = '[2017-10-27T09:32:15,286][INFO] Updated successfully'
        initial_message = self.client.readers.get(self.reader_1.reader_id).message
        self.assertNotEqual(desired_message, initial_message)

        self.client.readers.set_message(self.reader_1.reader_id, desired_message)

        final_message = self.client.readers.get(self.reader_1.reader_id).message
        self.assertEqual(final_message, desired_message)

    def test_set_mount(self):
        desired_mount = '/mnt-2'
        initial_mount = self.client.readers.get(self.reader_1.reader_id).mount
        self.assertNotEqual(desired_mount, initial_mount)

        self.client.readers.set_mount(self.reader_1.reader_id, desired_mount)

        final_mount = self.client.readers.get(self.reader_1.reader_id).mount
        self.assertEqual(final_mount, desired_mount)

    def test_find_by_fields_match(self):
        readers = self.client.readers.find_by_fields(hostname='ingest-station-1')
        readers = list(readers)
        self.assertEqual(len(readers), 1)
        self.assertEqual(readers[0].hostname, 'ingest-station-1')

        readers = self.client.readers.find_by_fields(device='/dev/md0')
        readers = list(readers)
        self.assertEqual(len(readers), 1)
        self.assertEqual(readers[0].device, '/dev/md0')

        readers = self.client.readers.find_by_fields(status=Reader.Status.EMPTY)
        readers = list(readers)
        self.assertEqual(len(readers), 1)
        self.assertEqual(readers[0].status, Reader.Status.EMPTY)

        readers = self.client.readers.find_by_fields(ingest_state=Reader.IngestState.IDLE)
        readers = list(readers)
        self.assertEqual(len(readers), 1)
        self.assertEqual(readers[0].ingest_state, Reader.IngestState.IDLE)

        readers = self.client.readers.find_by_fields(hostname='ingest-station-1',
                                                     device='/dev/md0',
                                                     status=Reader.Status.EMPTY,
                                                     ingest_state=Reader.IngestState.IDLE)
        readers = list(readers)
        self.assertEqual(len(readers), 1)
        self.assertEqual(readers[0].hostname, 'ingest-station-1')
        self.assertEqual(readers[0].device, '/dev/md0')
        self.assertEqual(readers[0].status, 'empty')
        self.assertEqual(readers[0].status, Reader.Status.EMPTY)
        self.assertEqual(readers[0].ingest_state, 'idle')
        self.assertEqual(readers[0].ingest_state, Reader.IngestState.IDLE)

    def test_find_by_fields_no_match(self):
        readers = self.client.readers.find_by_fields(hostname='ingest-station-2')
        readers = list(readers)
        self.assertEqual(len(readers), 0)

        readers = self.client.readers.find_by_fields(device='/dev/md1')
        readers = list(readers)
        self.assertEqual(len(readers), 0)

        readers = self.client.readers.find_by_fields(status='active')
        readers = list(readers)
        self.assertEqual(len(readers), 0)

        readers = self.client.readers.find_by_fields(ingest_state='processing')
        readers = list(readers)
        self.assertEqual(len(readers), 0)

        readers = self.client.readers.find_by_fields(hostname='ingest-station-2',
                                                     device='/dev/md0',
                                                     status=Reader.Status.EMPTY,
                                                     ingest_state=Reader.IngestState.IDLE)
        readers = list(readers)
        self.assertEqual(len(readers), 0)
