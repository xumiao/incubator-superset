from norm.executable import NormExecutable
from norm.executable.expression.condition import ConditionExpr
from norm.executable.expression.arithmetic import ArithmeticExpr


class ArgumentExpr(NormExecutable):

    def __init__(self, variable, expr, projection):
        """
        The argument expression, condition expressions and project to a new variable, or assignment expression
        :param variable: the variable
        :type variable: VariableName
        :param expr: the expression
        :type expr: Union[ConditionExpr, ArithmeticExpr]
        :param projection: the projection
        :type projection: Projection
        """
        super().__init__()
        self.variable = variable
        self.expr = expr
        self.projection = projection
        self.positional_variable = None

    def set_positional(self, var):
        self.positional_variable = var

    def execute(self, session, context):
        assignment = None
        condition = None
        projection = None
        if self.variable is None:
            # infer the original variable
            if isinstance(self.expr, ConditionExpr):
                # TODO: figure out the variable from the arithmetic expression
                self.variable = self.expr.aexpr
                condition = (self.variable.name, self.expr.op, self.expr.qexpr)
            else:
                self.variable = self.positional_variable
        if isinstance(self.expr, ArithmeticExpr):
            assignment = (self.variable.name, self.expr.execute(session, context))
        if self.projection is not None:
            projection = (self.variable.name, self.projection.variable_name.name)
        return assignment, condition, projection
