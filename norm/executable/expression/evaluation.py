from norm.literals import COP

from norm.executable import NormExecutable, NormError, Constant
from norm.executable.expression.argument import ArgumentExpr
from norm.executable.variable import VariableName
from norm.executable.expression import NormExpression

from typing import List, Union

import pandas as pd

import logging
logger = logging.getLogger(__name__)


class EvaluationExpr(NormExpression):

    def serialize(self):
        pass

    def __init__(self, args, variable=None):
        """
        The evaluation of an expression either led by a variable name
        :param args: the arguments provided
        :type args: List[ArgumentExpr]
        :param variable: the variable name to evaluate
        :type variable: VariableName
        """
        super().__init__()
        self.variable = variable
        self.args = args
        self.inputs = None
        self.outputs = None
        from norm.models.norm import Lambda
        self.lam = None   # type: Lambda
        self.is_to_add_data = False

    @property
    def is_constant_arguments(self):
        return all(isinstance(arg.expr, Constant) for arg in self.args)

    def check_assignment_arguments(self):
        """
        Check whether the arguments are in the style of assignments. Ex. 234, 'asfs', b=3, c=5
        :return: True or False
        :rtype: bool
        """
        keyword_arg = False  # positional argument
        for arg in self.args:
            if arg.op is None:
                assert(arg.variable is None)
                if keyword_arg:
                    msg = 'Keyword based arguments should come after positional arguments'
                    logger.error(msg)
                    raise NormError(msg)
            elif arg.op == COP.EQ:
                assert(arg.variable is not None)
                keyword_arg = True
            else:
                return False
        return True

    def build_assignment_inputs(self):
        """
        If the arguments are in assignment style, build the inputs as assignments
        :return: a dictionary mapping from a variable to an expression for the inputs
        :rtype: Dict
        """
        assert(self.lam is not None)
        nargs = len(self.args)
        assert(nargs <= self.lam.nargs)
        keyword_arg = False
        inputs = {}
        from norm.models.norm import Variable
        for ov, arg in zip(self.lam.variables[:nargs], self.args):  # type: Variable, ArgumentExpr
            if arg.op == COP.EQ:
                keyword_arg = True
            if not keyword_arg:
                inputs[ov.name] = arg.expr
            else:
                inputs[arg.variable.name] = arg.expr
        return inputs

    def build_conditional_inputs(self):
        """
        If the arguments are in conditional style, build the inputs as conditionals
        :return: a query string
        :rtype: Dict
        """
        assert(self.lam is not None)
        inputs = []
        for arg in self.args:
            # arg.expr should have been compiled
            if arg.op == COP.LK:
                condition = '{}.str.contains("{}")'.format(arg.variable, arg.expr)
            else:
                condition = '{} {} ({})'.format(arg.variable, arg.op, arg.expr)
            inputs.append(condition)
        return '({}) and ({})'.join(inputs)

    def build_outputs(self):
        """
        Build the outputs according to the projection
        :return: a dictionary mapping from the original variable to the new variable
        :rtype: Dict
        """
        assert(self.lam is not None)
        nargs = len(self.args)
        assert(nargs <= self.lam.nargs)
        keyword_arg = False
        outputs = {}
        from norm.models.norm import Variable
        for ov, arg in zip(self.lam.variables[:nargs], self.args):  # type: Variable, ArgumentExpr
            if arg.op == COP.EQ:
                keyword_arg = True
            if arg.projection is not None:
                assert (len(arg.projection.variables) == 1)
                assert (not arg.projection.to_evaluate)
                if not keyword_arg:
                    outputs[ov.name] = arg.projection.variables[0]
                else:
                    assert(arg.variable is not None)
                    outputs[arg.variable.name] = arg.projection.variables[0]
        return outputs

    def compile(self, context):
        if self.variable is None:
            from norm.models.norm import Lambda
            assert(context.scope is not None)
            assert(isinstance(context.scope, Lambda))
            self.lam = context.scope  # norm.models.norm.Lambda
            # constructing new objects
            assert(self.check_assignment_arguments())
            self.is_to_add_data = True
            self.inputs = self.build_assignment_inputs()
            self.outputs = None
        else:
            self.lam = self.variable.lam
            if self.check_assignment_arguments():
                self.inputs = self.build_assignment_inputs()
            else:
                self.inputs = self.build_conditional_inputs()
            self.outputs = self.build_outputs()
        return self

    def execute(self, context):
        if isinstance(self.inputs, dict):
            inputs = dict((key, value.execute(context)) for key, value in self.inputs)
        else:
            inputs = self.inputs
        return self.lam.query(inputs, self.outputs)


class ChainedEvaluationExpr(NormExpression):

    def __init__(self, lexpr, rexpr):
        """
        Chained evaluation expressions:
        Example:
        * a.b
        * a.test(sf, s)
        * a.b.c
        :param lexpr: base query expressions or chained expression
        :type lexpr: NormExpression
        :param rexpr: chained evaluation expression
        :type rexpr: Union[EvaluationExpr, VariableName]
        """
        super().__init__()
        self.lexpr = lexpr
        self.rexpr = rexpr
        self.lam = None

    def serialize(self):
        pass

    def compile(self, context):
        if isinstance(self.rexpr, VariableName):
            if isinstance(self.lexpr, VariableName):
                combined = VariableName(self.lexpr.name, self.rexpr).compile(context)
                if combined.lam:
                    # a.b already exists in the current scope
                    return combined
                if self.lexpr.lam.has_variable(self.rexpr.name):
                    # TODO: create a new Lambda of one field
                    pass
                # a.b where a exists but b does not ( to join with the Lambda of a )
                # TODO: join Lambda of a
                pass
            elif isinstance(self.lexpr, EvaluationExpr):
                if self.lexpr.lam.has_variable(self.rexpr.name):
                    # TODO: create a new Lambda of one field
                    pass
                else:
                    msg = '{} does not exist in the {}'.format(self.rexpr, self.lexpr)
                    logger.error(msg)
                    raise NormError(msg)
            # TODO: variable can be an function if no argument provided. a.name.count where count is a function
        elif isinstance(self.rexpr, EvaluationExpr):
            # Evaluation with the previous expression as the first input argument
            self.rexpr.args = [ArgumentExpr(None, None, self.lexpr, None)] + self.rexpr.args
            # Recompile the expression
            self.rexpr.compile(context)
            return self.rexpr
        return self

    def execute(self, context):
        lam = self.lexpr.execute(context)

        # TODO: Specialized to aggregations
        """
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
        """
        # TODO: deal with projection
        return lam
