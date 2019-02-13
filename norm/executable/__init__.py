from norm.literals import ConstantType


class Projection(object):

    def __init__(self, variables, to_evaluate=False):
        """
        The projection definition
        :param variables: a list of variables to project on
        :type variables: List[norm.executable.variable.VariableName]
        :param to_evaluate: whether to evaluate these variables or not, default to False.
        :type to_evaluate: Boolean
        """
        self.variables = variables
        self.to_evaluate = to_evaluate


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


class ListConstant(Constant):

    def __init__(self, type_, value):
        """
        A list of constant of the same constant type
        :param type_: the name of the constant type
        :type type_: ConstantType
        :param value: the value of the constant
        :type value: List
        """
        assert(isinstance(value, list))
        super().__init__(type_, value)


class NormError(RuntimeError):
    pass


class NormExecutable(object):

    def compile(self, context):
        """
        Compile the command with the given context
        :param context: the context of the executable
        :type context: norm.engine.NormCompiler
        """
        raise NotImplementedError

    def execute(self, context):
        """
        Execute the command with given context
        :param context: the context of the executable
        :type context: norm.engine.NormCompiler
        :return: pandas.DataFrame
        :rtype: pandas.DataFrame
        """
        raise NotImplementedError()

