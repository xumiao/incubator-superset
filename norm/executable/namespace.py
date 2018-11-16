from norm.executable import NormExecutable
from norm.executable.type import TypeName

import logging

logger = logging.getLogger(__name__)


class ImportVariable(NormExecutable):

    def __init__(self, namespace=None, type_=None, variable=None):
        """
        Import the namespace, if the type name and the variable name are given, save the given type as the variable.
        :param namespace: the namespace
        :type namespace: str
        :param type_: the type
        :type type_: TypeName
        :param variable: the variable
        :type variable: str
        """
        super().__init__()
        self.namespace = namespace
        self.type_ = type_
        if variable is None and type_ is not None:
            self.variable = type_.name
        else:
            self.variable = variable

    def execute(self, session, user, context):
        if self.namespace:
            context.namespaces.add(self.namespace)
        if self.type_:
            if self.namespace:
                self.type_.namespace = self.namespace
            lam = self.type_.execute(session, user, context)
            if self.variable in context.variables:
                logger.warning("Variable {} has already in the memory. Will be replaced".format(self.variable))
            context.variables[self.variable] = lam
        return self.namespace
