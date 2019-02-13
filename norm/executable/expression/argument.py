from norm.executable import NormError
from norm.executable.expression import NormExpression
from norm.executable.expression.condition import ConditionExpr
from norm.executable.expression.arithmetic import ArithmeticExpr

import logging

from norm.literals import ROP

logger = logging.getLogger(__name__)


class ArgumentExpr(NormExpression):

    def __init__(self, variable, op, expr, projection):
        """
        The argument expression project to a new variable, either assigning or conditional.
        :param variable: the variable
        :type variable: VariableName
        :param expr: the arithmetic expression for the variable
        :type expr: ArithmeticExpr
        :param op: the operation, assignment or conditional
        :type op: ROP or AOP
        :param projection: the projection
        :type projection: Projection
        """
        super().__init__()
        self.variable = variable
        self.expr = expr
        self.op = op
        self.projection = projection

    def compile(self, context):
        if self.variable is None:
            msg = 'variable is required for execution on an argument expression'
            logger.error(msg)
            raise NormError(msg)

        assignment = None
        condition = None
        projection = None
        if self.op == ROP.ASS:
            assignment = (self.variable.name, self.expr.execute(context))
        if isinstance(self.expr, ArithmeticExpr):
            assignment = (self.variable.name, self.expr.execute(context))
        if self.projection is not None:
            projection = (self.variable.name, self.projection.variable_name.name)
        return assignment, condition, projection

    def execute(self, context):
        if self.variable is None:
            msg = 'variable is required for execution on an argument expression'
            logger.error(msg)
            raise NormError(msg)

        assignment = None
        condition = None
        projection = None
        if self.op == ROP.ASS:
            assignment = (self.variable.name, self.expr.execute(context))
        if isinstance(self.expr, ArithmeticExpr):
            assignment = (self.variable.name, self.expr.execute(context))
        if self.projection is not None:
            projection = (self.variable.name, self.projection.variable_name.name)
        return assignment, condition, projection
