from unittest import TestCase

from dmsclient import factories


class CartridgeModelTestCase(TestCase):
    attributes_to_verify = [
        'cartridge_id',
        'device',
        'ingest_station',
        'usage',
        'workflow_type',
        'ingest_state',
        'slot',
        'updated_at'
    ]

    def __init__(self, *args, **kwargs):
        super(CartridgeModelTestCase, self).__init__(*args, **kwargs)
        self.cartridge_1 = factories.CartridgeFactory()

    def test_verify_attributes(self):
        for attr in self.attributes_to_verify:
            self.assertTrue(hasattr(self.cartridge_1, attr))

    def test_verify_dict_keys(self):
        d = self.cartridge_1.to_dict()
        for attr in self.attributes_to_verify:
            self.assertIn(attr, d)

    def test_invalid_cartridge_id(self):
        with self.assertRaises(ValueError) as error:
            factories.CartridgeFactory(cartridge_id='')
        self.assertEqual('cartridge_id must be a non-empty string', str(error.exception))

    def test_invalid_ingest_station(self):
        with self.assertRaises(ValueError) as error:
            factories.CartridgeFactory(ingest_station='')
        self.assertEqual('ingest_station must be a non-empty string', str(error.exception))

    def test_invalid_device(self):
        with self.assertRaises(ValueError) as error:
            factories.CartridgeFactory(device='')
        self.assertEqual('device must be a non-empty string', str(error.exception))

    def test_invalid_workflow_type(self):
        with self.assertRaises(ValueError) as error:
            factories.CartridgeFactory(workflow_type='fake-workflow')
        self.assertEqual("'fake-workflow' is not a valid WorkflowType", str(error.exception))

    def test_invalid_ingest_state(self):
        with self.assertRaises(ValueError) as error:
            factories.CartridgeFactory(ingest_state='fake-state')
        self.assertEqual("'fake-state' is not a valid IngestState",
                         str(error.exception))

    def test_invalid_usage(self):
        with self.assertRaises(ValueError) as error:
            factories.CartridgeFactory(usage="abc")
        self.assertEqual('usage must be a number', str(error.exception))

    def test_invalid_slot(self):
        with self.assertRaises(ValueError) as error:
            factories.CartridgeFactory(slot=100)
        self.assertEqual('slot must be a string', str(error.exception))

    def test_invalid_updated_at(self):
        with self.assertRaises(ValueError) as error:
            factories.CartridgeFactory(updated_at='2017-10-22T10:30:43')
        self.assertEqual('updated_at must be of type datetime', str(error.exception))
