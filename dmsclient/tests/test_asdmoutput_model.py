from unittest import TestCase

from dmsclient import factories
from dmsclient.models.asdmoutput import AsdmOutput


class AsdmOutputModelTestCase(TestCase):

    def __init__(self, *args, **kwargs):
        super(AsdmOutputModelTestCase, self).__init__(*args, **kwargs)
        self.asdmoutput_1 = factories.AsdmOutputFactory()

    def test_verify_attributes(self):
        for attr in AsdmOutput.PROTECTED_ATTRIBUTES:
            self.assertTrue(hasattr(self.asdmoutput_1, attr))

    def test_verify_attributes_from_elasticsearch(self):
        document = {'_source': self.asdmoutput_1.to_dict()}

        d = AsdmOutput.from_elasticsearch(document)

        for attr in AsdmOutput.PROTECTED_ATTRIBUTES:
            self.assertTrue(hasattr(d, attr))
