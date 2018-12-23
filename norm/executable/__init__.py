from norm.literals import ConstantType


class Projection(object):

    def __init__(self, limit, variable_name):
        """
        The projection definition
        :param limit: the limit of the query
        :type limit: int
        :param variable_name: the name of the variable to project to
        :type variable_name: norm.executable.variable.VariableName
        """
        self.limit = limit
        self.variable_name = variable_name


class Constant(object):

    def __init__(self, type_, value):
        """
        The constant
        :param type_: the name of the constant type, e.g.,
                      [none, bool, integer, float, string, unicode, pattern, uuid, url, datetime]
        :type type_: ConstantType
        :param value: the value of the constant
        :type value: Union[str, unicode, int, float, bool, datetime.datetime, NoneType]
        """
        super().__init__()
        self.type_ = type_  # type: ConstantType
        self.value = value


class NormError(RuntimeError):
    pass


class NormExecutable(object):

    def __init__(self):
        """
        Build an executable from the expression command
        """
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

    def execute(self, context):
        """
        Execute the command with given context
        :param context: the context of the executable
        :type context: norm.engine.NormCompiler
        :return: pandas.DataFrame
        :rtype: pandas.DataFrame
        """
        raise NotImplementedError()

