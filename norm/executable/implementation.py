from norm.executable import NormExecutable


class TypeImplementation(NormExecutable):

    def __init__(self, type_name, op, query, description):
        """
        The implementation of a type. Depending on the operation, it can be initial implementation or
        incremental implementation.
        :param type_name: the type to implement
        :type type_name: TypeName
        :param op: the operation of the implementation, i.e., ['=', '|=', '&=']
        :type op: ImplType
        :param query: the query expression that implements the type
        :type query: QueryExpr
        :param description: the implementation documentation. it will be appended to original one for incremental.
        :type description: str
        """
        super().__init__()
        self.type_name = type_name
        self.op = op
        self.query = query
        self.description = description

    def execute(self, session, user, context):
        # TODO: implement
        pass

