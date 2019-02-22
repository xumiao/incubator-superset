from norm.executable import NormError, Constant
from norm.literals import COP, ConstantType

from norm.executable.expression import NormExpression
from norm.executable.expression.assignment import AssignmentExpr
from norm.executable.variable import VariableName

import logging
logger = logging.getLogger(__name__)


class ConditionExpr(NormExpression):

    def __init__(self, op, lexpr, rexpr):
        """
        Condition expression
        :param op: conditional operation, e.g., [<, <=, >, >=, =, !=, in, !in, ~]. ~ means 'like'
        :type op: COP
        :param lexpr: arithmetic expression, e.g., a + b - c
        :type lexpr: ArithmeticExpr
        :param rexpr: another arithmetic expression
        :type rexpr: ArithmeticExpr
        """
        super().__init__()
        self.op = op
        self.lexpr = lexpr
        self.rexpr = rexpr
        self._condition = None
        assert(self.lexpr is not None)
        assert(self.rexpr is not None)
        assert(self.op is not None)

    def __str__(self):
        if self._condition is None:
            msg = 'Compile the condition expression first'
            logger.error(msg)
            raise NormError(msg)
        return self._condition

    def compile(self, context):
        if self._condition is not None:
            return self

        if isinstance(self.lexpr, VariableName) and not self.lexpr.exists(context):
            if self.op == COP.EQ:
                return AssignmentExpr(self.lexpr, self.rexpr)
            else:
                msg = 'Can not find the variable {} in the current context'.format(self.lexpr)
                logger.error(msg)
                raise NormError(msg)
        else:
            self.lexpr = self.lexpr.compile(context)
            self.rexpr = self.rexpr.compile(context)
            if self.op == COP.LK:
                assert(isinstance(self.lexpr, VariableName))
                assert(isinstance(self.rexpr, Constant))
                assert(self.rexpr.type_ is ConstantType.STR or self.rexpr.type_ is ConstantType.PTN)
                self._condition = '{}.str.contains("{}")'.format(self.lexpr, self.rexpr)
            else:
                self._condition = '({}) {} ({})'.format(self.lexpr, self.op, self.rexpr)
        return self

    def serialize(self):
        pass

    def execute(self, context):
        # TODO query the condition
        pass


class CombinedConditionExpr(ConditionExpr):

    def __init__(self, op, lexpr, rexpr):
        """
        Combined conditional expression
        :param op: logical operation, e.g., ['and', 'or'] others are not supported yet # TODO support xor, imp, eqv
        :type op: LOP
        :param lexpr: left conditional expression
        :type lexpr: ConditionExpr
        :param rexpr:right conditional expression
        :type rexpr: ConditionExpr
        """
        super().__init__(op, lexpr, rexpr)

    def compile(self, context):
        if self._condition is not None:
            return self

        self.lexpr = self.lexpr.compile(context)
        self.rexpr = self.rexpr.compile(context)
        self._condition = '({}) {} ({})'.format(self.lexpr, self.op, self.rexpr)
        return self
