from norm.executable import NormExecutable
from norm.executable.expression.base import NormExpression


class SliceExpr(NormExpression):

    def __init__(self, expr, start, end):
        """
        Slice the expression results
        :param expr: the expression to evaluate
        :type expr: NormExecutable
        :param start: the start position
        :type start: int
        :param end: the end position
        :type end: int
        """
        super().__init__()
        self.expr = expr
        self.start = start
        self.end = end
        self._projection = None

    def execute(self, session, context):
        df = self.expr.execute(session, context)
        df = df.iloc[self.start:self.end]
        # TODO reset the index for the projected variable
        return df
