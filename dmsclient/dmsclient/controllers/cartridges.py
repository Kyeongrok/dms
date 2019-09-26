from dmsclient.controllers import DMSControllerWithState
from dmsclient.models.cartridge import Cartridge
from dmsclient.models.reader import Reader


class CartridgeController(DMSControllerWithState):
    """
    Controller class for  manipulating cartridges
    """
    @property
    def model_class(self):
        return Cartridge

    def set_ingest_state(self, cartridge_id, ingest_state):
        """
        Update the cartridge ingest state for the document matching the given ID.

        :param cartridge_id: the cartridge ID to be updated
        :type cartridge_id: string
        :param ingest_state: the desired ingest state (valid states found in
        `dmsclient.models.reader.Reader.INGEST_STATES`)
        :type ingest_state: string
        :raises ValueError: if the ingest state is not valid
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(cartridge_id, {'ingest_state': Reader.IngestState(ingest_state)})

    def set_workflow_type(self, cartridge_id, workflow_type):
        """
        Update the cartridge workflow_type for the document matching the given ID.

        :param cartridge_id: the cartridge ID to be updated
        :type cartridge_id: string
        :param workflow_type: the ingestion type (valid states found in
        `dmsclient.models.cartridge.Cartridge.WORKFLOW_TYPE`)
        :type workflow_type: string
        :raises ValueError: if the workflow type is not valid
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(cartridge_id, {'workflow_type': Cartridge.WorkflowType(workflow_type)})

    def set_usage(self, cartridge_id, usage):
        """
        Update the usage for the document matching the given ID.

        :param cartridge_id: the cartridge ID to be updated
        :type cartridge_id: string
        :param usage: the amount of data in the cartridge
        :type usage: double
        :raises ValueError: if usage is not a number
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(cartridge_id, {'usage': usage})