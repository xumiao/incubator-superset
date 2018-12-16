import pandas as pd

from norm.executable.expression.base import NormExpression


class ArithmeticExpr(NormExpression):

    def __init__(self, constant, variable_name, op, expr1, expr2=None):
        """
        Arithmetic expression
        :param constant: a constant
        :type constant: Constant
        :param variable_name: a variable
        :type variable_name: VariableName
        :param op: the operation, e.g., [+, -, *, /, %, **]
        :type op: AOP
        :param expr1: left expression
        :type expr1: ArithmeticExpr
        :param expr2: right expression
        :type expr2: ArithmeticExpr
        """
        super().__init__()
        self.constant = constant
        self.variable_name = variable_name
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
        self._projection = None

    def execute(self, session, context):
        # TODO
        if self.constant:
            try:
                context.df[self.projection.variable_name.name] = self.constant.value
                return context.df
            except:
                return pd.DataFrame(data=[self.constant.value], columns=['value'])


