import pandas as pd

from norm.executable import NormExecutable
from norm.models.norm import Lambda


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
        lam = self.variable_type.execute(session, user, context)
        assert(lam is not None)

        from norm.models.norm import Variable
        var = session.query(Variable).filter(Variable.name == self.variable_name.name,
                                             Variable.type_id == lam.id).scalar()
        if var is None:
            return Variable(self.variable_name.name, lam)
        else:
            return var


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
        self.namespace = None
        self.description = None

    def execute(self, session, user, context):
        # TODO: optimize to query db in batch for all types or utilize cache
        variables = [var_declaration.execute(session, user, context) for var_declaration in
                     reversed(self.argument_declarations)]
        self.type_name.namespace = self.namespace
        lam = self.type_name.execute(session, user, context)  # type: Lambda
        if lam.id is None:
            # lam is newly created
            lam.description = self.description
            lam.variables = variables
            session.add(lam)
        else:
            # lam might be modified
            # TODO: use sqlalchemy session to determine whether lam is dirty or not
            dirty = False
            if self.description and lam.description != self.description:
                lam.description = self.description
                dirty = True
            if lam.variables != variables:
                lam.variables = variables
                dirty = True
            if dirty:
                lam.new_version(session)
        session.commit()
        return pd.DataFrame(data=[['succeed', '{} has been created'.format(lam.signature)]],
                            columns=['status', 'message'])
