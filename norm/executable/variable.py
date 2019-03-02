from norm.executable import NormExecutable


class VariableName(NormExecutable):

    def __init__(self, name, attribute=None):
        """
        The variable and its recursive attributes
        :param name: the variable name
        :type name: str
        :param attribute: the attribute of the variable, could be nested
        :type attribute: VariableName
        """
        super().__init__()
        if attribute is None:
            self.name = name
        else:
            self.name = name + '.' + attribute.name
        self.lam = None

    def exists(self, context):
        """
        TODO: Check whether context contains the variable
        """
        pass

    def compile(self, context):
        # TODO: create or retrieve the lambda for the current variable
        return self
