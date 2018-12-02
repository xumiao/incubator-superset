from norm.executable import NormExecutable, NormError
from norm.executable.type import TypeName

import logging

from norm.models.mixins import new_version
from norm.models.norm import Status

logger = logging.getLogger(__name__)


class ImportVariable(NormExecutable):

    def __init__(self, namespace=None, type_=None, variable=None):
        """
        Import the namespace, if the variable name is given, the imported type is cloned to the
        current context with the variable name
        :param namespace: the namespace
        :type namespace: str
        :param type_: the type
        :type type_: TypeName
        :param variable: the variable
        :type variable: str
        """
        super().__init__()
        assert(namespace is not None)
        assert(namespace != '')
        self.namespace = namespace
        self.type_ = type_
        self.variable = variable

    def execute(self, session, context):
        """
        Imports follow the following logic:
            * imported namespace is stored in the context
            * imported type is cloned in the context namespace as a draft
            * imported type with alias is cloned and renamed in the context namespace as a draft
        """
        context.search_namespaces.add(self.namespace)
        if self.type_:
            self.type_.namespace = self.namespace
            lam = self.type_.execute(session, context)
            if lam is None:
                msg = "Can not find the type {} in namespace {}".format(self.type_.name, self.namespace)
                raise NormError(msg)
            alias = lam.clone()
            alias.namespace = context.context_namespace
            if self.variable:
                alias.name = self.variable
            assert(alias.version is None)
            session.add(alias)
        return self.namespace


class ExportVariable(NormExecutable):

    def __init__(self, namespace=None, type_=None, alias=None):
        """
        Export the type to the namespace
        :param namespace: the namespace
        :type namespace: str
        :param type_: the type
        :type type_: TypeName
        :param alias: the alias in the namespace
        :type alias: str
        """
        super().__init__()
        assert(namespace is not None)
        assert(namespace != '')
        assert(type_ is not None)
        self.namespace = namespace
        self.type_ = type_
        self.alias = alias

    def execute(self, session, context):
        lam = self.type_.execute(session, context)
        if lam is None:
            msg = "Can not find the type {} in namespace {}".format(self.type_.name, self.type_.namespace)
            raise NormError(msg)
        lam.namespace = self.namespace
        if self.alias:
            lam.name = self.alias
        lam.version = new_version(lam.namespace, lam.name)
        lam.status = Status.READY
        return lam
