from sqlalchemy.orm import with_polymorphic
from sqlalchemy import desc

from norm.executable import NormExecutable, NormError
from superset.models.natives import ListLambda
from superset.models.norm import Lambda


class TypeName(NormExecutable):

    DEFAULT_VERSION = 1
    DEFAULT_NAMESPACE = ''

    def __init__(self, name, version=None):
        """
        The type qualified name
        :param name: name of the type
        :type name: str
        :param version: version of the type
        :type version: int
        """
        super().__init__()
        self.namespace = None
        self.name = name
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
        if self.namespace is not None:
            namespaces = [self.namespace]
        else:
            namespaces = context.namespaces

        if self.version is None:
            #  find the latest version
            lam = session.query(with_polymorphic(Lambda, '*')) \
                .filter(Lambda.namespace.in_(namespaces),
                        Lambda.name == self.name,
                        Lambda.owners.in_([user, None]))\
                .order_by(desc(Lambda.version))\
                .first()
        else:
            lam = session.query(with_polymorphic(Lambda, '*')) \
                .filter(Lambda.namespace.in_(namespaces),
                        Lambda.name == self.name,
                        Lambda.version == self.version,
                        Lambda.owners.in_([user, None]))\
                .first()

        if lam is None:
            #  create a new Lambda
            # TODO: namespace should be default to user
            namespace = self.namespace or self.DEFAULT_NAMESPACE
            version = self.version or self.DEFAULT_VERSION
            lam = Lambda(namespace=namespace, name=self.name, version=version, user=user)

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
        if lam.id is None:
            raise NormError("{} does not seem to be declared yet".format(self.intern))

        llam = session.query(ListLambda).filter(ListLambda.variables == [lam]).first()
        if llam is None:
            # create a new ListLambda
            llam = ListLambda(lam)

        return llam
