from norm.executable import NormExecutable
from norm.executable.expression.argument import ArgumentExpr
from norm.executable.variable import VariableName
from norm.executable.expression.base import NormExpression


import pandas as pd


class EvaluationExpr(NormExpression):

    def __init__(self, type_name, args):
        """
        The evaluation of an expression either led by a type name or a variable name
        :param type_name: the type name or the variable name
        :type type_name: TypeName
        :param args: the arguments provided
        :type args: List[ArgumentExpr]
        """
        super().__init__()
        self.type_name = type_name
        self.args = args
        self._projection = None

    def execute(self, session, context):
        lam = self.type_name.execute(session, context)
        if lam is None:
            raise RuntimeError('Given type {} is not found'.format(self.type_name))
        nargs = lam.nargs
        if len(self.args) > nargs:
            raise RuntimeError('Given type {} has less number of variables defined'.format(self.type_name))
        assignments = []
        projections = []
        conditions = []
        for i, arg in enumerate(reversed(self.args)):  # type: ArgumentExpr
            arg.set_positional(lam.variables[i])
            assignment, condition, projection = arg.execute(session, context)
            assignments.append(assignment)
            conditions.append(condition)
            projections.append(projection)

        # TODO: to project the type index itself
        return lam.query(assignments, conditions, projections)


class ChainedEvaluationExpr(NormExpression):

    def __init__(self, lexpr, rexpr):
        """
        Chained evaluation expressions
        :param lexpr: base query expressions or chained expression
        :type lexpr: NormExecutable
        :param rexpr: chained evaluation expression
        :type rexpr: Union[EvaluationExpr, VariableName]
        """
        super().__init__()
        self.lexpr = lexpr
        self.rexpr = rexpr
        self._projection = None

    def execute(self, session, context):
        df = self.lexpr.execute(session, context)

        # TODO: Specialized to aggregations
        if isinstance(self.rexpr, EvaluationExpr):
            agg_expr = self.rexpr
            agg_exp = agg_expr.type_name.name
            if agg_exp == 'Distinct':
                df = df.drop_duplicates()
                df = df.reset_index()
            elif agg_exp == 'Count':
                df = pd.DataFrame(df.count()).reset_index().rename(columns={"index": "column", 0: "count"})
            elif agg_exp == 'Order':
                arg = self.rexpr.args[0].expr
                col = arg.aexpr.value
                df = df.sort_values(by=col)
        elif isinstance(self.rexpr, VariableName):
            # TODO: check whether the property is correct
            return df[[self.rexpr.name]]

        # TODO: deal with projection
        return df
