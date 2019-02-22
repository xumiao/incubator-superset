from norm.executable.expression import NormExpression, Projection
from norm.executable.expression.condition import ConditionExpr, CombinedConditionExpr
from norm.literals import LOP

import logging
logger = logging.getLogger(__name__)


class QueryExpr(NormExpression):

    def __init__(self, op, expr1, expr2):
        """
        Query expression
        :param op: logical operation, e.g., [&, |, ^, =>, <=>]
        :type op: LOP
        :param expr1: left expression
        :type expr1: NormExpression
        :param expr2: right expression
        :type expr2: NormExpression
        """
        super().__init__()
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2

    def compile(self, context):
        self.expr1 = self.expr1.compile(context)
        self.expr2 = self.expr2.compile(context)
        if isinstance(self.expr1, ConditionExpr) and isinstance(self.expr2, ConditionExpr):
            return CombinedConditionExpr(self.op, self.expr1, self.expr2)
        return self

    def serialize(self):
        pass

    def execute(self, context):
        lam1 = self.expr1.execute(context)
        lam2 = self.expr2.execute(context)
        # TODO: AND to intersect, OR to union
        return lam2


class NegatedQueryExpr(NormExpression):

    def __init__(self, expr):
        """
        Negation of the expression
        :param expr: the expression to negate
        :type expr: NormExpression
        """
        super().__init__()
        self.expr = expr

    def compile(self, context):
        if isinstance(self.expr, QueryExpr):
            self.expr.expr1 = NegatedQueryExpr(self.expr.expr1).compile(context)
            self.expr.expr2 = NegatedQueryExpr(self.expr.expr2).compile(context)
            self.expr.op = self.expr.op.negate()
        elif isinstance(self.expr, ConditionExpr):
            self.expr.op = self.expr.op.negate()
        else:
            msg = 'Currently NOT only works on logically combined query or conditional query'
            logger.error(msg)
            raise NotImplementedError(msg)
        return self.expr

    def serialize(self):
        pass

    def execute(self, context):
        pass


class ProjectedQueryExpr(NormExpression):

    def __init__(self, expr, projection):
        """
        Project query expression
        :param expr: the expression to project
        :type expr: NormExpression
        :param projection: the projection
        :type projection: Projection
        """
        super().__init__()
        self.expr = expr
        self.projection = projection

    def compile(self, context):
        self.expr = self.expr.compile(context)
        self.expr.projection = self.projection
        return self.expr

    def serialize(self):
        pass

    def execute(self, context):
        pass
