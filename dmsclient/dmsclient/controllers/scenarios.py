from dmsclient.controllers import DMSControllerWithState
from dmsclient.models.scenario import Scenario


class ScenarioController(DMSControllerWithState):
    """
    Controller class for manipulating Scenario documents
    """

    @property
    def model_class(self):
        return Scenario
