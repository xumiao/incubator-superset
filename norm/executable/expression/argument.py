from norm.literals import COP

from norm.executable import Projection
from norm.executable.variable import VariableName
from norm.executable.expression import NormExpression
from norm.executable.expression.arithmetic import ArithmeticExpr

import logging

logger = logging.getLogger(__name__)


class ArgumentExpr(NormExpression):

    def __init__(self, variable, op, expr, projection):
        """
        The argument expression project to a new variable, either assigning or conditional.
        :param variable: the variable
        :type variable: VariableName or None
        :param expr: the arithmetic expression for the variable
        :type expr: ArithmeticExpr or None
        :param op: the conditional operation
        :type op: COP or None
        :param projection: the projection
        :type projection: Projection or None
        """
        super().__init__()
        self.variable = variable
        self.expr = expr
        self.op = op
        self.projection = projection

    def serialize(self):
        pass
