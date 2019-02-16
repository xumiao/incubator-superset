from norm.executable import NormExecutable
from norm.executable.expression.argument import ArgumentExpr
from norm.executable.type import TypeName
from norm.executable.variable import VariableName
from norm.executable.expression import NormExpression


import pandas as pd


class EvaluationExpr(NormExpression):

    def __init__(self, variable, args):
        """
        The evaluation of an expression either led by a type name or a variable name
        :param variable: the variable name to evaluate
        :type variable: VariableName
        :param args: the arguments provided
        :type args: List[ArgumentExpr]
        """
        super().__init__()
        self.variable = variable
        self.args = args
        self.projections = None
        self.filters = None
        self.lam = None

    def compile(self, context):
        # compile the variable from context
        self.lam = TypeName(self.variable.name).compile(context)

        # compile the arguments
        for i, arg in enumerate(self.args):  # type: ArgumentExpr
            arg.projection
            arg.set_positional(lam.variables[i])
            assignment, condition, projection = arg.execute(context)
            assignments.append(assignment)
            conditions.append(condition)
            projections.append(projection)

        if projections is None:
            df = pd.read_parquet(self.data_file)
        else:
            df = pd.read_parquet(self.data_file, columns=[col[0] for col in projections])
            df = df.rename(columns=dict(projections))
        if filters:
            projections = dict(projections)
            from norm.literals import COP
            for col, op, value in filters:
                pcol = projections.get(col, col)
                df = df[df[pcol].notnull()]
                if op == COP.LK:
                    df = df[df[pcol].str.contains(value.value)]
                elif op == COP.GT:
                    df = df[df[pcol] > value.value]
                elif op == COP.GE:
                    df = df[df[pcol] >= value.value]
                elif op == COP.LT:
                    df = df[df[pcol] < value.value]
                elif op == COP.LE:
                    df = df[df[pcol] <= value.value]
                elif op == COP.EQ:
                    df = df[df[pcol] == value.value]
                elif op == COP.NE:
                    if value.value is not None:
                        df = df[df[pcol] != value.value]
                elif op == COP.IN:
                    # TODO: Wrong
                    df = df[df[pcol].isin(value.value)]
                elif op == COP.NI:
                    # TODO: Wrong
                    df = df[~df[pcol].isin(value.value)]
        return df
        # TODO: might optimize the arguments
        pass

    def execute(self, context):
        # execute arguments
        context.get_variable()
        lam = self.type_name.execute(context)
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
            assignment, condition, projection = arg.execute(context)
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

    def execute(self, context):
        df = self.lexpr.execute(context)

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
