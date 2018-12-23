from norm.executable import NormExecutable, NormError
from norm.models import Lambda, Status

import logging
logger = logging.getLogger(__name__)


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

    def execute(self, context):
        session = context.session
        # TODO: joinly search the type for the variable
        lam = self.variable_type.execute(context)
        if lam is None:
            msg = "Type {} for variable {} has not been declared yet"\
                .format(self.variable_type.name, self.variable_name)
            raise NormError(msg)

        from norm.models import Variable
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

    def execute(self, context):
        """
        Declare a type:
            * Create a type
            * Add new variable to a type # TODO
            * Modify description # TODO
            * Modify variables # TODO
        :return: the lambda
        :rtype: Lambda
        """
        session = context.session
        # TODO: optimize to query db in batch for all types or utilize cache
        variables = [var_declaration.execute(context) for var_declaration in
                     reversed(self.argument_declarations)]
        self.type_name.namespace = context.context_namespace
        lam = self.type_name.execute(context)  # type: Lambda
        if lam is None:
            #  Create a new Lambda
            lam = Lambda(namespace=context.context_namespace, name=self.type_name.name)
            lam.description = self.description
            lam.variables = variables
            session.add(lam)
            return lam
        else:
            assert(lam.status == Status.DRAFT)
            # Revise the existing schema
            current_variable_names = set(v.name for v in lam.variables)
            new_variable_names = set(v.name for v in variables)
            lam.delete_variable(*current_variable_names.difference(new_variable_names))
            lam.astype(*variables)
            lam.add_variable(*variables)
            # TODO: make a doc change revision
            if self.description:
                lam.description = self.description

