from norm.executable import NormExecutable


class ConditionExpr(NormExecutable):

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
        self._projection = None

    def execute(self, session, user, context):
        # TODO filtering the df by the condition
        pass