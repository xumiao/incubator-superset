from norm.executable.expression import NormExpression, Projection
from norm.executable.expression.evaluation import EvaluationExpr
from norm.executable.variable import VariableName
from norm.literals import LOP

import pandas as pd


class QueryExpr(NormExpression):

    def __init__(self, op, expr1, expr2):
        """
        Query expression
        :param op: logical operation, e.g., [&, |, !, =>, <=>]
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

    def execute(self, context):
        df = None
        if self.op is None:
            self.expr1.projection = self.projection
            df = self.expr1.execute(context)
        elif self.op == LOP.AND:
            df = self.expr1.execute(context)
            if not df.empty:
                pass
            if isinstance(self.expr2, EvaluationExpr):
                # TODO: move to natives
                if self.expr2.name and self.expr2.name.name == 'Extract':
                    col = self.expr2.args[1].expr.aexpr.name
                    pt = self.expr2.args[0].expr.aexpr.value
                    import re
                    def extract(x):
                        s = re.search(pt, x)
                        return s.groups()[0] if s else None
                    var_name = self.expr2.projection.variable_name.name
                    df[var_name] = df[col].apply(extract)
                else:
                    df2 = self.expr2.execute(context)
                    df = pd.concat([df, df2], axis=1)
        return df


class NegatedQueryExpr(NormExpression):

    def __init__(self, expr):
        """
        Negation of the expression
        :param expr: the expression to negate
        :type expr: NormExpression
        """
        super().__init__()
        self.expr = expr

    def execute(self, context):
        raise NotImplementedError


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

    def execute(self, context):
        raise NotImplementedError


class AssignedQueryExpr(NormExpression):

    def __init__(self, expr, variable):
        """
        Assign query result to a variable
        :param expr: the expression
        :type expr: NormExpression
        :param variable: the variable to be assigned to
        :type variable: VariableName
        """
        super().__init__()
        self.expr = expr
        self.variable = variable

    def execute(self, context):
        raise NotImplementedError
