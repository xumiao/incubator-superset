from norm.executable import NormExecutable


class VariableName(NormExecutable):

    def __init__(self, variable, attribute=None):
        """
        The variable and its recursive attributes
        :param variable: the variable
        :type variable: VariableName
        :param attribute: the attribute of the variable
        :type attribute: str
        """
        super().__init__()
        self.variable = variable
        self.attribute = attribute

    @property
    def name(self):
        if isinstance(self.variable, VariableName):
            return self.variable.name + '.' + self.attribute
        else:
            return self.variable

    def compile(self, context):
        pass

    def execute(self, context):
        pass
