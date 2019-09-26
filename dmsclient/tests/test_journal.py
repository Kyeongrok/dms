from dmsclient.models.journal import Journal
from tests import BaseTestCase


class JournalTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(JournalTestCase, self).__init__(*args, **kwargs)
        self.journal_1 = Journal(log_level='INFO',
                                 ingest_station='station-1',
                                 context='context-1',
                                 message='action 1 status 1',
                                 field_1='field-1',
                                 field_2='field-2')

    def setUp(self):
        super(JournalTestCase, self).setUp()
        self.client.journals.create(self.journal_1)

    def tearDown(self):
        super(JournalTestCase, self).tearDown()
        self.client.journals.delete_all()

    def test_find_journal(self):
        journals = self.client.journals.find_by_fields(context='context-1')

        journals = list(journals)
        self.assertGreaterEqual(len(journals), 1)
        self.assertEqual(journals[0].log_level, 'INFO')
        self.assertEqual(journals[0].ingest_station, 'station-1')
        for field in journals[0].extra_fields:
            self.assertIn(field, journals[0].extra_fields)

    def test_invalid_log_level(self):
        with self.assertRaises(ValueError) as error:
            Journal(log_level='INVALID',
                    ingest_station='station-1',
                    context='context-1',
                    message='action 1 status 1')
        self.assertEqual("log level must be one of the following: ('INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG')",
                         str(error.exception))
