from sqlalchemy.orm import with_polymorphic

from norm.executable import NormExecutable
from superset.models.natives import ListLambda
from superset.models.norm import Lambda


class TypeName(NormExecutable):
    DEFAULT_VERSION = 1

    def __init__(self, name, version):
        """
        The type qualified name
        :param name: name of the type
        :type name: str
        :param version: version of the type
        :type version: int
        """
        super().__init__()
        self.name = name
        self.namespace = None
        if version is None:
            self.version = self.DEFAULT_VERSION
        else:
            self.version = version

    def __str__(self):
        return self.name + '@' + str(self.version)

    def execute(self, session, user, context):
        """
        Retrieve the Lambda function by namespace, name, version.
        Note that user is encoded by the version.
        :rtype: Lambda
        """
        # TODO: handle exceptions
        if self.namespace:
            lam = session.query(with_polymorphic(Lambda, '*')) \
                .filter(Lambda.namespace == self.namespace, Lambda.name == self.name, Lambda.version == self.version) \
                .first()
        else:
            lam = session.query(with_polymorphic(Lambda, '*')) \
                .filter(Lambda.name == self.name, Lambda.version == self.version) \
                .first()
        return lam


class ListType(NormExecutable):

    def __init__(self, intern):
        """
        The type of List with intern type
        :param intern: the type of the intern
        :type intern: TypeName
        """
        super().__init__()
        self.intern = intern

    def execute(self, session, user, context):
        """
        Return a list type
        :rtype: ListLambda
        """
        lam = self.intern.execute(session, user, context)
        if lam is None:
            raise RuntimeError("{} does not seem to be declared yet".format(self.intern))
        return ListLambda(lam)


class UnionType(NormExecutable):

    def __init__(self, types):
        """
        The type of union of types. Either one of these types
        :param types: the types to union
        :type types: List[TypeName]
        """
        super().__init__()
        self.types = types
