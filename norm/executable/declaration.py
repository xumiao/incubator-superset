import pandas as pd

from norm.executable import NormExecutable


class ArgumentDeclaration(NormExecutable):

    def __init__(self, variable_name, variable_type):
        """
        The argument declaration
        :param variable_name: the name of the variable
        :type variable_name: VariableName
        :param variable_type: the type of the variable
        :type variable_type: TypeName
        """
        super().__init__()
        self.variable_name = variable_name
        self.variable_type = variable_type

    def execute(self, session, user, context):
        """
        Create variables or retrieve variables
        :rtype: superset.models.norm.Variable
        """
        from superset.models.norm import Variable

        return Variable(self.variable_name.name,
                        self.variable_type.execute(session, user, context))


class TypeDeclaration(NormExecutable):

    def __init__(self, type_name, argument_declarations, output_type_name):
        """
        The type declaration in full format
        :param type_name: the type name
        :type type_name: TypeName
        :param argument_declarations: the list of argument declarations
        :type argument_declarations: List[ArgumentDeclaration]
        :param output_type_name: the type_name as output, default to boolean
        :type output_type_name: TypeName
        """
        super().__init__()
        self.type_name = type_name
        self.argument_declarations = argument_declarations
        self.output_type_name = output_type_name
        self.expr = None
        self.namespace = ''
        self.description = ''

    def create_lambda(self, namespace, description, params, variables, user):
        from superset.models.norm import Lambda
        name = self.type_name.name
        version = self.type_name.version
        code = self.expr.code()
        return Lambda(namespace=namespace, name=name, version=version, description=description, params=params,
                      variables=variables, code=code, user=user)

    def execute(self, session, user, context):
        # TODO: optimize to query db in batch for all types or utilize cache
        variables = [var_declaration.execute(session, user, context) for var_declaration in
                     reversed(self.argument_declarations)]
        # TODO: extract description from comments
        lam = self.type_name.execute(session, user, context)
        if not lam:
            lam = self.create_lambda(self.namespace, self.description, '{}', variables, user)
            session.add(lam)
        else:
            # TODO: deal with versioning
            lam.variables = variables
            lam.code = self.expr.code()

        session.commit()
        return pd.DataFrame(data=[['succeed', '{} has been created'.format(lam.signature)]],
                            columns=['status', 'message'])
