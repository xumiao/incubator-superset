from norm.executable import NormExecutable
from norm.executable import Projection


class NormExpression(NormExecutable):

    def __init__(self):
        super().__init__()
        self._query = ''
        self._projection = None  # type: Projection

    @property
    def projection(self):
        return self._projection

    @projection.setter
    def projection(self, value):
        """
        :param value: set the projection
        :type value: Projection
        """
        self._projection = value

    @property
    def query(self):
        """
        Generate compiled query string
        :return: str
        """
        return self._query

    def execute(self, context):
        raise NotImplementedError
