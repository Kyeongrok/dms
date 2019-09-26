from dmsclient.controllers import DMSController
from dmsclient.models.asdmoutput import AsdmOutput


class AsdmOutputController(DMSController):
    """
    Controller class for manipulating AsdmOutput documents
    """

    @property
    def model_class(self):
        return AsdmOutput
