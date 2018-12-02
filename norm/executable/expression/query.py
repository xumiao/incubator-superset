from norm.executable import NormExecutable
from norm.executable.expression.evaluation import EvaluationExpr
from norm.literals import LOP

import pandas as pd


class QueryExpr(NormExecutable):

    def __init__(self, op, expr1, expr2, projection):
        """
        Query expression
        :param op: logical operation, e.g., [&, |, !, =>, <=>]
        :type op: LOP
        :param expr1: left expression
        :type expr1: NormExecutable
        :param expr2: right expression
        :type expr2: NormExecutable
        """
        super().__init__()
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
        self.projection = projection

    def execute(self, session, context):
        df = None
        if self.op is None:
            self.expr1.projection = self.projection
            df = self.expr1.execute(session, context)
        elif self.op == LOP.AND:
            df = self.expr1.execute(session, context)
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
                    df2 = self.expr2.execute(session, user)
                    df = pd.concat([df, df2], axis=1)
        return df