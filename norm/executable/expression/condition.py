from norm.executable.expression import NormExpression


class ConditionExpr(NormExpression):

    def __init__(self, op, lexpr, rexpr):
        """
        Condition expression
        :param op: conditional operation, e.g., [<, <=, >, >=, ==, !=, in, !in, ~]. ~ means 'like'
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

    def execute(self, context):
        # TODO filtering the df by the condition
        pass
