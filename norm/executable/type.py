from norm.executable import NormExecutable, NormError
from norm.models.natives import ListLambda
from norm.models.norm import Lambda, Variable, retrieve_type, Status


class TypeName(NormExecutable):

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
        assert(self.name is not None)
        assert(self.name != '')

    def __str__(self):
        s = self.namespace if self.namespace else ''
        s += '.' + self.name
        s += '@' + str(self.version) if self.version is not None else ''
        return s

    def execute(self, session, context, to_create=False):
        """
        Retrieve the Lambda function by namespace, name, version.
        Note that user is encoded by the version.
        :rtype: Lambda
        """
        if self.namespace is None:
            lam = retrieve_type(context.context_namespace, self.name, self.version, session)
            if lam is None:
                lam = retrieve_type(context.search_namespaces, self.name, self.version, session, Status.READY)
        else:
            if self.namespace == context.context_namespace:
                lam = retrieve_type(self.namespace, self.name, self.version, session)
            else:
                lam = retrieve_type(self.namespace, self.name, self.version, session, Status.READY)

        if lam is None and to_create:
            #  create a new Lambda
            lam = Lambda(namespace=self.namespace or context.context_namespace,
                         name=self.name)
            session.add(lam)
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

    def execute(self, session, context):
        """
        Return a list type
        :rtype: ListLambda
        """
        lam = self.intern.execute(session, context)
        if lam.id is None:
            raise NormError("{} does not seem to be declared yet".format(self.intern))

        llam = session.query(ListLambda, Variable).join(ListLambda.variables)\
                      .filter(Variable.type_id == lam.id)\
                      .scalar()
        if llam is None:
            # create a new ListLambda
            llam = ListLambda(lam)
            session.add(llam)
        return llam
