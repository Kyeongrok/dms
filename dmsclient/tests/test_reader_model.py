from unittest import TestCase

from dmsclient import factories


class ReaderModelTestCase(TestCase):
    attributes_to_verify = [
        'reader_id',
        'hostname',
        'device',
        'status',
        'ingest_state',
        'message',
        'port',
        'updated_at'
    ]

    def __init__(self, *args, **kwargs):
        super(ReaderModelTestCase, self).__init__(*args, **kwargs)
        self.reader_1 = factories.ReaderFactory()

    def test_verify_attributes(self):
        for attr in self.attributes_to_verify:
            self.assertTrue(hasattr(self.reader_1, attr))

    def test_verify_dict_keys(self):
        d = self.reader_1.to_dict()
        for attr in self.attributes_to_verify:
            self.assertIn(attr, d)

    def test_invalid_reader_id(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(reader_id='')
        self.assertEqual('reader_id must be a non-empty string', str(error.exception))

    def test_invalid_hostname(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(hostname='')
        self.assertEqual('hostname must be a non-empty string', str(error.exception))

    def test_invalid_device(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(device='')
        self.assertEqual('device must be a non-empty string', str(error.exception))

    def test_invalid_status(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(status='fake-status')
        self.assertEqual("'fake-status' is not a valid Status", str(error.exception))

    def test_invalid_ingest_state(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(ingest_state='fake-state')
        self.assertEqual("'fake-state' is not a valid IngestState",
                         str(error.exception))

    def test_invalid_message(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(message=123)
        self.assertEqual('message must be a string', str(error.exception))

    def test_invalid_mount(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(mount=456)
        self.assertEqual('mount must be a string', str(error.exception))

    def test_invalid_port(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(port=100)
        self.assertEqual('port must be a string', str(error.exception))

    def test_invalid_updated_at(self):
        with self.assertRaises(ValueError) as error:
            factories.ReaderFactory(updated_at='2017-10-22T10:30:43')
        self.assertEqual('updated_at must be of type datetime', str(error.exception))
