from norm.executable import NormExecutable


class VariableName(NormExecutable):

    def __init__(self, variable, attribute):
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
        return self.variable.name + '.' + self.attribute

    def execute(self, session, user, context):
        """

        :param session:
        :param user:
        :param context:
        :return:
        """
        pass
