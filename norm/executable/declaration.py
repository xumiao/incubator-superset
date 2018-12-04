import pandas as pd

from norm.executable import NormExecutable, NormError
from norm.models.norm import Lambda, Status


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

    def execute(self, session, context):
        """
        Create variables or retrieve variables
        :rtype: superset.models.norm.Variable
        """
        lam = self.variable_type.execute(session, context)
        if lam is None:
            msg = "Type {} for variable {} has not been declared yet"\
                .format(self.variable_type.name, self.variable_name)
            raise NormError(msg)

        from norm.models.norm import Variable
        var = session.query(Variable).filter(Variable.name == self.variable_name.name,
                                             Variable.type_id == lam.id).scalar()
        if var is None:
            var = Variable(self.variable_name.name, lam)
            session.add(var)
        return var


class TypeDeclaration(NormExecutable):

    def __init__(self, type_name, argument_declarations, output_type_name):
        """
        The type declaration
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
        self.description = None

    def execute(self, session, context):
        """
        Declare a type:
            * Create a type
            * Add new variable to a type # TODO
            * Modify description # TODO
            * Modify variables # TODO
        :return: the lambda
        :rtype: Lambda
        """
        # TODO: optimize to query db in batch for all types or utilize cache
        variables = [var_declaration.execute(session, context) for var_declaration in
                     reversed(self.argument_declarations)]
        self.type_name.namespace = context.context_namespace
        lam = self.type_name.execute(session, context, to_create=True)  # type: Lambda
        if lam.status == Status.DRAFT:
            # If the lambda is a draft, we revise directly
            lam.description = self.description
            lam.variables = variables
            return lam
        else:
            # If the lambda is ready, we clone to the context first and revise.
            new_lam = lam.clone()
            new_lam.description = self.description
            new_lam.variables = variables
            new_lam.status = Status.DRAFT
            new_lam.namespace = context.context_namespace
            return new_lam
