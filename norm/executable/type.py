from norm.executable import NormExecutable, NormError
from norm.models import ListLambda, Lambda, PythonLambda, Variable, retrieve_type, Status


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

    def execute(self, context):
        """
        Retrieve the Lambda function by namespace, name, version.
        Note that user is encoded by the version.
        :rtype: Lambda
        """
        session = context.session
        if self.namespace is None:
            lam = retrieve_type(context.context_namespace, self.name, self.version, session)
            if lam is None:
                lam = retrieve_type(context.search_namespaces, self.name, self.version, session, Status.READY)
        else:
            if self.namespace == context.context_namespace:
                lam = retrieve_type(self.namespace, self.name, self.version, session)
            elif self.namespace.startswith('python'):
                lam = retrieve_type(self.namespace, self.name, self.version, session, Status.READY)
                if lam is None:
                    # create a new PythonLambda
                    d = {}
                    exec('from {} import {}'.format(self.namespace[7:], self.name), d)
                    v = d.get(self.name)
                    if not callable(v):
                        msg = '{} from {} is not a python function'.format(self.name, self.namespace)
                        raise NormError(msg)
                    # TODO: decide output type and package version
                    lam = PythonLambda(namespace=self.namespace, name=self.name, description=v.__doc__)
                    session.add(lam)
            else:
                lam = retrieve_type(self.namespace, self.name, self.version, session, Status.READY)
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

    def execute(self, context):
        """
        Return a list type
        :rtype: ListLambda
        """
        lam = self.intern.execute(context)
        if lam.id is None:
            raise NormError("{} does not seem to be declared yet".format(self.intern))

        q = context.session.query(ListLambda, Variable).join(ListLambda.variables)\
                           .filter(Variable.type_id == lam.id)
        llam = q.scalar()
        if llam is None:
            # create a new ListLambda
            llam = ListLambda(lam)
            context.session.add(llam)
        return llam
