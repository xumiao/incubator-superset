from antlr4 import *
import re
from dateutil import parser as dateparser
from sqlalchemy import exists
import pandas as pd
from typing import List, Union

from sqlalchemy.orm import with_polymorphic

from norm.literals import AOP, COP, LOP, CodeMode, ConstantType
from norm.normLexer import normLexer
from norm.normParser import normParser
from norm.normListener import normListener
from norm import config
from antlr4.error.ErrorListener import ErrorListener

from superset.models.norm import Lambda
from superset.models.natives import ListLambda


class NormErrorListener(ErrorListener):

    def __init__(self):
        super(NormErrorListener, self).__init__()

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        err_msg = "line " + str(line) + ":" + str(column) + " " + msg
        raise ValueError(err_msg)


class NormExecutable(object):
    """
    Execute Norm Command
    """
    context = None  # type: NormCompiler

    def __init__(self):
        """
        Build an executable from the expression command
        """
        pass

    def execute(self, session, user):
        """
        Execute the command with given session and user context
        :param session: The session the command is executed against
        :type session: sqlalchemy.orm.Session
        :param user: The user model
        :return: pandas.DataFrame
        :type: pandas.DataFrame
        """
        raise NotImplementedError()


class VariableName(NormExecutable):

    def __init__(self, name, attribute):
        """
        The name of the variable
        :type name: str
        """
        super().__init__()
        self.name = name
        self.attribute = attribute

    @property
    def variable(self):
        if self.attribute:
            return self.name + '.' + self.attribute
        else:
            return self.name

    def execute(self, session, user):
        """
        If variable already exists in the context variables or the dataframe, fetch it.
        Otherwise, return the name itself
        :rtype: Union[pd.DataFrame, str]
        """
        if self.name in self.context.variables:
            df = self.context.variables.get(self.name)
            if self.attribute is not None:
                return df[[self.attribute]]
            else:
                return df

        variable = self.variable
        if variable in self.context.df:
            return self.context.df[[variable]]
        else:
            return self.variable


class TypeName(NormExecutable):

    def __init__(self, name, version):
        """
        The type qualified name
        :param name: name of the type
        :type name: str
        :param version: version of the type
        :type version: int
        """
        super().__init__()
        self.name = name
        if version is None:
            self.version = 1

    def __str__(self):
        return self.name + '@' + str(self.version)

    def execute(self, session, user):
        """
        Retrieve the Lambda function by namespace, name, version.
        Note that user is encoded by the version.
        :rtype: Lambda
        """
        # TODO: figure out namespace imports
        # TODO: handle exceptions
        lam = session.query(with_polymorphic(Lambda, '*')) \
            .filter(Lambda.name == self.name, Lambda.version == self.version) \
            .first()
        return lam


class ListType(NormExecutable):

    def __init__(self, intern):
        """
        The type of List with intern type
        :param intern: the type of the intern
        :type intern: TypeName
        """
        super().__init__()
        self.intern = intern

    def execute(self, session, user):
        """
        Return a list type
        :rtype: ListLambda
        """
        lam = self.intern.execute(session, user)
        if lam is None:
            raise ParseError("{} does not seem to be declared yet".format(self.intern))

        return ListLambda(lam)


class UnionType(NormExecutable):

    def __init__(self, types):
        """
        The type of union of types. Either one of these types
        :param types: the types to union
        :type types: List[TypeName]
        """
        super().__init__()
        self.types = types

    def execute(self, session, user):
        """
        Union type should be used as a literal for now
        """
        raise NotImplementedError("UnionType is only a literal of the AST for now, not executable")


class TypeDefinition(NormExecutable):

    def __init__(self, type_name, argument_declarations, output_type_name):
        """
        The definition of a type.
        :param type_name: the type name
        :type type_name: TypeName
        :param argument_declarations: the list of argument declarations
        :type argument_declarations: List[ArgumentDeclaration]
        :param output_type_name: the type_name as output, default to boolean
        :type output_type_name: TypeName
        """
        super().__init__()
        self.type_name = type_name
        self.argument_declarations = argument_declarations
        self.output_type_name = output_type_name

    def execute(self, session, user):
        """
        Should be used as a literal for now
        """
        msg = "{} is only a literal of the AST for now, not executable".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class TypeImpl(NormExecutable):

    def __init__(self, mode, code):
        """
        The implementation of the type
        :param mode: the mode of the implementation, query, python or keras
        :type mode: CodeMode
        :param code: the code of the implementation
        :type code: str
        """
        super().__init__()
        self.mode = mode
        self.code = code

    def execute(self, session, user):
        """
        Should be used as a literal for now
        """
        msg = "{} is only a literal of the AST for now, not executable".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class ArgumentDeclaration(NormExecutable):

    def __init__(self, variable_name, variable_type):
        """
        The argument declaration
        :param variable_name: the name of the variable
        :type variable_name: VariableName
        :param variable_type: the type of the variable
        :type variable_type: TypeName
        """
        super().__init__()
        self.variable_name = variable_name
        self.variable_type = variable_type

    def execute(self, session, user):
        """
        Create variables or retrieve variables
        :rtype: superset.models.norm.Variable
        """
        from superset.models.norm import Variable

        return Variable(self.variable_name.name,
                        self.variable_type.execute(session, user))


class TypeDeclaration(NormExecutable):

    def __init__(self, type_definition, type_implementation):
        """
        The type declaration in full format
        :param type_definition: the definition of the type
        :type type_definition: Union[TypeName, TypeDefinition]
        :param type_implementation: the implementation of the type
        :type type_implementation: TypeImpl
        """
        super().__init__()
        self.type_definition = type_definition
        self.type_implementation = type_implementation

    def execute(self, session, user):
        """
        Should be used as a literal for now
        """
        msg = "{} is only a literal of the AST for now, not executable".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class FullTypeDeclaration(TypeDeclaration):

    def __init__(self, type_definition, type_implementation):
        """
        The type declaration in full format
        :param type_definition: the definition of the type
        :type type_definition: TypeDefinition
        :param type_implementation: the implementation of the type
        :type type_implementation: TypeImpl
        """
        super().__init__(type_definition, type_implementation)

    @staticmethod
    def create_lambda(mode, namespace, name, version, description, params, variables, code, user):
        from superset.models.norm import Lambda, PythonLambda, KerasLambda
        L = Lambda
        if mode == CodeMode.PYTHON:
            L = PythonLambda
        elif mode == CodeMode.KERAS:
            L = KerasLambda
        return L(namespace=namespace, name=name, version=version, description=description, params=params,
                 variables=variables, code=code, user=user)

    def execute(self, session, user):
        namespace = self.context.namespace
        type_def = self.type_definition
        type_name = type_def.type_name.name
        type_version = type_def.type_name.version
        # TODO: optimize to query db in batch for all types or utilize cache
        variables = [var_declaration.execute(session, user) for var_declaration in type_def.argument_declarations]
        # TODO: extract description from comments
        lam = type_def.type_name.execute(session, user)
        if not lam:
            lam = self.create_lambda(self.type_implementation.mode, namespace, type_name, type_version, '',
                                     '{}', variables, self.type_implementation.code, user)
            session.add(lam)
        else:
            # TODO: deal with versioning
            lam.variables = variables
            lam.code = self.type_implementation.code

        session.commit()
        return pd.DataFrame(data=[['succeed', '{} has been created'.format(lam.signature)]],
                            columns=['status', 'message'])


class IncrementalTypeDeclaration(TypeDeclaration):

    def __init__(self, type_name, type_implementation):
        """
        The incremental type declaration
        :param type_name: the type name to append on
        :type type_name: TypeName
        :param type_implementation: the implementation of the type
        :type type_implementation: TypeImpl
        """
        super().__init__(type_name, type_implementation)

    def execute(self, session, user):
        lam = self.type_definition.execute(session, user)
        if not lam:
            return pd.DataFrame(data=[['failed', '{} has not been declared yet'.format(self.type_definition.name)]])
        else:
            # TODO: deal with versioning
            lam.code += ' | ' + self.type_implementation.code

        session.commit()
        return pd.DataFrame(data=[['succeed', '{} has been created'.format(lam.signature)]],
                            columns=['status', 'message'])


class Projection(NormExecutable):

    def __init__(self, limit, variable_name):
        """
        The projection definition
        :param limit: the limit of the query
        :type limit: int
        :param variable_name: the name of the variable to project to
        :type variable_name: VariableName
        """
        super().__init__()
        self.limit = limit
        self.variable_name = variable_name

    def execute(self, session, user):
        """
        Should be used as a literal for now
        """
        msg = "{} is only a literal of the AST for now, not executable".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class Constant(NormExecutable):

    def __init__(self, type_, value):
        """
        The constant
        :param type_: the name of the constant type, e.g.,
                      [none, bool, integer, float, string, unicode, pattern, uuid, url, datetime]
        :type type_: ConstantType
        :param value: the value of the constant
        :type value: Union[str, unicode, int, float, bool, datetime.datetime, NoneType]
        """
        super().__init__()
        self.type_ = type_
        self.value = value

    def execute(self, session, user):
        """
        Should be used as a literal for now
        """
        msg = "{} is only a literal of the AST for now, not executable".format(self.__class__.__name__)
        raise NotImplementedError(msg)


QueryExpr = Union[Constant, VariableName, TypeName, "EvaluationExpr", "AssignmentExpr", "ArithmeticExpr",
                  "CombinedExpr", "ConditionExpr", "ConditionCombinedExpr", "ChainedEvaluationExpr",
                  List["QueryExpr"]]


class ArgumentExpr(NormExecutable):

    def __init__(self, expr, projection):
        """
        The argument expression, condition expressions and project to a new variable, or assignment expression
        :param expr: the expression
        :type expr: QueryExpr
        :param projection: the projection
        :type projection: Projection
        """
        super().__init__()
        self.expr = expr
        self.projection = projection

    def execute(self, session, user):
        """
        Should be used as a literal for now
        """
        msg = "{} is only a literal of the AST for now, not executable".format(self.__class__.__name__)
        raise NotImplementedError(msg)


class EvaluationExpr(NormExecutable):

    def __init__(self, name, args, projection):
        """
        The evaluation of an expression either led by a type name or a variable name
        :param name: the type name or the variable name
        :type name: Union[TypeName, VariableName]
        :param args: the arguments provided
        :type args: List[ArgumentExpr]
        :param projection: projected to a variable
        :type projection: Projection
        """
        super().__init__()
        self.name = name
        self.args = args
        self.projection = projection

    def execute(self, session, user):
        #  imports = self.context.imports
        if isinstance(self.name, TypeName):
            if self.name.name == 'Concat':
                df1 = self.args[0].expr.execute(session, user)
                df2 = self.args[1].expr.execute(session, user)
                df = pd.concat([df1, df2], axis=1)
                return df
            # TODO: figure out how to search through all namespaces
            lam = self.name.execute(session, user)
            projections = []
            filters = []
            for arg in self.args:
                original_variable = None
                if arg.expr and isinstance(arg.expr, VariableName):
                    original_variable = arg.expr
                elif arg.expr and isinstance(arg.expr, ConditionExpr):
                    cexpr = arg.expr
                    original_variable = cexpr.aexpr
                    assert(isinstance(original_variable, VariableName))
                    filters.append((original_variable.name, cexpr.op, cexpr.qexpr))

                project_variable = arg.projection.variable_name
                if original_variable is None and project_variable is not None:
                    projections.append((project_variable.name, project_variable.name))
                elif original_variable is not None and project_variable is None:
                    projections.append((original_variable.name, original_variable.name))
                elif original_variable is not None and project_variable is not None:
                    projections.append((original_variable.name, project_variable.name))
                else:
                    raise Exception('No original variable nor project variable')

            return lam.query(filters, projections)
        elif isinstance(self.name, VariableName):
            df = self.context.variables.get(self.name.name)
            if df is not None:
                projections = []
                filters = []
                for arg in self.args:
                    original_variable = None
                    if arg.expr and isinstance(arg.expr, VariableName):
                        original_variable = arg.expr
                    elif arg.expr and isinstance(arg.expr, ConditionExpr):
                        cexpr = arg.expr
                        original_variable = cexpr.aexpr
                        assert (isinstance(cexpr.qexpr, Constant))
                        filters.append((original_variable.name, cexpr.op, cexpr.qexpr))

                    project_variable = arg.projection.variable_name
                    if original_variable is None and project_variable is not None:
                        projections.append((project_variable.name, project_variable.name))
                    elif original_variable is not None and project_variable is None:
                        projections.append((original_variable.name, original_variable.name))
                    elif original_variable is not None and project_variable is not None:
                        projections.append((original_variable.name, project_variable.name))
                    else:
                        raise Exception('No original variable nor project variable')
                if filters:
                    for col, op, value in filters:
                        df = df[df[col].notnull()]
                        if op == COP.LK:
                            df = df[df[col].str.contains(value.value)]
                        elif op == COP.GT:
                            df = df[df[col] > value.value]
                        elif op == COP.GE:
                            df = df[df[col] >= value.value]
                        elif op == COP.LT:
                            df = df[df[col] < value.value]
                        elif op == COP.LE:
                            df = df[df[col] <= value.value]
                        elif op == COP.EQ:
                            df = df[df[col] == value.value]
                        elif op == COP.NE:
                            if value.value is not None:
                                df = df[df[col] != value.value]
                        elif op == COP.IN:
                            # TODO: Wrong
                            df = df[df[col].isin(value.value)]
                        elif op == COP.NI:
                            # TODO: Wrong
                            df = df[~df[col].isin(value.value)]
                if projections:
                    df = df.rename(columns=dict(projections))
                return df[[col[1] for col in projections]]


class ArithmeticExpr(NormExecutable):

    def __init__(self, op, expr1, expr2):
        """
        Arithmetic operation over two expressions
        :param op: the operation, e.g., [+, -, *, /, %]
        :type op: AOP
        :param expr1: left expression
        :type expr1: QueryExpr
        :param expr2: right expression
        :type expr2: QueryExpr
        """
        super().__init__()
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2

    def execute(self, session, user):
        pass


class AssignmentExpr(NormExecutable):

    def __init__(self, variable_name, expr):
        """
        Assignment
        :param variable_name: the variable name
        :type variable_name: VariableName
        :param expr: the expression to be evaluated
        :type expr: QueryExpr
        """
        super().__init__()
        self.variable_name = variable_name
        self.expr = expr

    def execute(self, session, user):
        v = self.variable_name.name
        df = self.expr.execute(session, user)
        self.context.variables[v] = df
        return df


class ConditionExpr(NormExecutable):

    def __init__(self, op, aexpr, qexpr):
        """
        Condition expression
        :param op: conditional operation, e.g., [<, <=, >, >=, ==, !=, in, !in, ~]. ~ means 'like'
        :type op: COP
        :param aexpr: arithmetic expression, e.g., a + b - c
        :type aexpr: ArithmeticExpr
        :param qexpr: query expression that evaluates to a constant
        :type qexpr: QueryExpr
        """
        super().__init__()
        self.op = op
        self.aexpr = aexpr
        self.qexpr = qexpr

    def execute(self, session, user):
        pass


class CombinedExpr(NormExecutable):

    def __init__(self, op, expr1, expr2):
        """
        Combining two expression together by logical operation
        :param op: logical operation, e.g., [&, |, !]
        :type op: LOP
        :param expr1: left expression
        :type expr1: QueryExpr
        :param expr2: right expression
        :type expr2: QueryExpr
        """
        super().__init__()
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2

    def execute(self, session, user):
        if self.op == LOP.AND:
            df = self.expr1.execute(session, user)  # type: pd.DataFrame
            if not df.empty:
                pass
            if isinstance(self.expr2, EvaluationExpr):
            # TODO: move to natives
                if self.expr2.name and self.expr2.name.name == 'Extract':
                    col = self.expr2.args[0].expr.name
                    pt = self.expr2.args[1].expr.value
                    import re
                    def extract(x):
                        s = re.search(pt, x)
                        return s.groups()[0] if s else None
                    var_name = self.expr2.projection.variable_name.name
                    df[var_name] = df[col].apply(extract)
            return df


class ChainedEvaluationExpr(NormExecutable):

    def __init__(self, qexpr, eexpr):
        """
        Chained evaluation expressions
        :param qexpr: query expression
        :type qexpr: QueryExpr
        :param eexpr: chained evaluation expression
        :type eexpr: Union[EvaluationExpr, VariableName]
        """
        super().__init__()
        self.qexpr = qexpr
        self.eexpr = eexpr

    def execute(self, session, user):
        df = self.qexpr.execute(session, user)

        # TODO: Specialized to aggregations

        agg_expr = self.eexpr  # type: EvaluationExpr
        agg_exp = agg_expr.name.name
        if agg_exp == 'Distinct':
            df = df.drop_duplicates()
        elif agg_exp == 'Count':
            df = pd.DataFrame(df.count()).reset_index().rename(columns={"index": "column", 0: "count"})
        elif agg_exp == 'Order':
            arg = self.eexpr.args[0].expr
            col = arg.expr.value
            df = df.sort_values(by=col)
        elif agg_exp == 'Take':
            start = self.eexpr.args[0].expr.value
            end = None
            if isinstance(self.eexpr.args[1].expr, ArithmeticExpr):
                expr = self.eexpr.args[1].expr  # type: ArithmeticExpr
                if expr.op == AOP.SUB:
                    end = -expr.expr1.value
            else:
                end = self.eexpr.args[1].expr.value
            if end is None:
                df = df.iloc[start:]
            else:
                df = df.iloc[start:end]

        return df.reset_index()


class PropertyExpr(ChainedEvaluationExpr):

    def __init__(self, qexpr, eexpr):
        """
        Access a property from qexpr result
        :param qexpr: query expression
        :type qexpr: QueryExpr
        :param eexpr: the property variable name
        :type eexpr: VariableName
        """
        super().__init__(qexpr, eexpr)

    def execute(self, session, user):
        df = self.qexpr.execute(session, user)
        # TODO: check whether the property is correct
        return df[[self.eexpr.name]]


class ParseError(ValueError):
    pass


class NormSyntaxError(ValueError):
    pass


class NormCompiler(normListener):

    def __init__(self):
        self.comments = ''
        self.imports = []
        self.namespace = ''
        self.alias = {}
        self.variables = {}
        self.stack = []
        self.df = pd.DataFrame()
        self.clear()
        self.walker = ParseTreeWalker()

    def clear(self):
        self.comments = ''
        self.imports = []
        self.namespace = ''
        self.alias = {}
        self.variables = {}
        self.stack = []
        self.df = pd.DataFrame()

    @staticmethod
    def trim_script(script):
        statements = script.split(';')
        if len(statements) > 1:
            to_compile = [s for s in statements if s.find("namespace") > -1 or s.find("import") > -1]
            last_statement = statements[-2] + ";"
            if last_statement.find("namespace") < 0 and last_statement.find("import") < 0:
                to_compile.append(last_statement)
            else:
                to_compile[-1] += ';'
            script = ';'.join(to_compile)
        return script

    def optimize(self):
        """
        Optimize the AST to have a more efficient execution plan
        # TODO
        * Filtering conditions can be combined and executed in batch instead of sequential
        * Arithmetic equations can be combined and passed to DF in batch instead of sequential
        """
        pass

    def set_execution_context(self):
        NormExecutable.context = self

    def compile(self, script, cont=False, last=True):
        # if not cont:
        #    self.clear()
        script = script.strip(' \r\n\t')
        if last:
            script = self.trim_script(script)
        script = script.strip(' \r\n\t')
        if script == '':
            return None

        self.set_execution_context()

        lexer = normLexer(InputStream(script))
        stream = CommonTokenStream(lexer)
        parser = normParser(stream)
        parser.addErrorListener(NormErrorListener())
        tree = parser.script()
        self.walker.walk(self, tree)
        self.optimize()
        return self.stack.pop()

    def exitNone(self, ctx:normParser.NoneContext):
        self.stack.append(Constant(ConstantType.NULL, None))

    def exitBool_c(self, ctx:normParser.Bool_cContext):
        self.stack.append(Constant(ConstantType.BOOL, ctx.getText().lower() == 'true'))

    def exitInteger_c(self, ctx:normParser.Integer_cContext):
        self.stack.append(Constant(ConstantType.INT, int(ctx.getText())))

    def exitFloat_c(self, ctx:normParser.Float_cContext):
        self.stack.append(Constant(ConstantType.FLT, float(ctx.getText())))

    def exitString_c(self, ctx:normParser.String_cContext):
        self.stack.append(Constant(ConstantType.STR, str(ctx.getText()[1:-1])))

    def exitUnicode_c(self, ctx:normParser.Unicode_cContext):
        self.stack.append(Constant(ConstantType.UNC, str(ctx.getText()[2:-1]).encode(config.UNICODE, 'ignore')))

    def exitPattern(self, ctx:normParser.PatternContext):
        try:
            self.stack.append(Constant(ConstantType.PTN, re.compile(str(ctx.getText()[2:-1]))))
        except:
            raise ValueError('Pattern constant {} is in wrong format, should be Python regex pattern'
                             .format(ctx.getText()))

    def exitUuid(self, ctx:normParser.UuidContext):
        self.stack.append(Constant(ConstantType.UID, str(ctx.getText()[2:-1])))

    def exitUrl(self, ctx:normParser.UrlContext):
        self.stack.append(Constant(ConstantType.URL, str(ctx.getText()[2:-1])))

    def exitDatetime(self, ctx:normParser.DatetimeContext):
        self.stack.append(Constant(ConstantType.DTM, dateparser.parse(ctx.getText()[2:-1], fuzzy=True)))

    def exitQueryLimit(self, ctx:normParser.QueryLimitContext):
        lmt = ctx.getText()
        if lmt == '*':
            self.stack.append(config.MAX_LIMIT)
            return

        try:
            lmt = int(lmt)
            if lmt < 0:
                raise ValueError('Query limit must be positive integer, but we get {}'.format(lmt))
        except:
            raise ValueError('Query limit must be positive integer, but we get {}'.format(lmt))
        self.stack.append(lmt)

    def exitQueryProjection(self, ctx:normParser.QueryProjectionContext):
        variable = self.stack.pop() if ctx.variableName() else None
        lmt = self.stack.pop() if ctx.querySign().queryLimit() else None
        self.stack.append(Projection(lmt, variable))

    def exitArgumentExpression(self, ctx:normParser.ArgumentExpressionContext):
        projection = self.stack.pop() if ctx.queryProjection() else None
        expr = self.stack.pop() if ctx.queryExpression() else None
        self.stack.append(ArgumentExpr(expr, projection))

    def exitArgumentExpressions(self, ctx:normParser.ArgumentExpressionsContext):
        args = []
        for ch in ctx.children:
            if isinstance(ch, normParser.ArgumentExpressionContext):
                args.append(self.stack.pop())
        if not all([isinstance(arg, ArgumentExpr) for arg in args]):
            raise ParseError('Parsing Error, not all arguments parsed correctly')
        self.stack.append(list(reversed(args)))

    def exitEvaluationExpression(self, ctx:normParser.EvaluationExpressionContext):
        projection = self.stack.pop() if ctx.queryProjection() else None
        args = self.stack.pop() if ctx.argumentExpressions() else []
        variable_name = self.stack.pop() if ctx.variableName() else None
        type_name = self.stack.pop() if ctx.typeName() else None
        if variable_name is None and type_name is None:
            raise ParseError('Evaluation expression at least starts with a type or a variable')
        self.stack.append(EvaluationExpr(type_name or variable_name, args, projection))

    def exitArithmeticExpression(self, ctx:normParser.ArithmeticExpressionContext):
        if ctx.constant() or ctx.variableName() or ctx.listExpression() is not None or ctx.LBR():
            return
        if ctx.MINUS():
            expr = self.stack.pop()
            self.stack.append(ArithmeticExpr(AOP.SUB, expr, None))
            return
        if ctx.spacedArithmeticOperator():
            expr2 = self.stack.pop()
            expr1 = self.stack.pop()
            aop = AOP(ctx.spacedArithmeticOperator().arithmeticOperator().getText())
            self.stack.append(ArithmeticExpr(aop, expr1, expr2))

    def exitAssignmentExpression(self, ctx:normParser.AssignmentExpressionContext):
        expr = self.stack.pop()
        variable_name = self.stack.pop()
        self.stack.append(AssignmentExpr(variable_name, expr))

    def exitConditionExpression(self, ctx:normParser.ConditionExpressionContext):
        qexpr = self.stack.pop()
        aexpr = self.stack.pop()
        cop = COP(ctx.spacedConditionOperator().conditionOperator().getText())
        self.stack.append(ConditionExpr(cop, aexpr, qexpr))

    def exitListExpression(self, ctx:normParser.ListExpressionContext):
        exprs = []
        for ch in ctx.children:
            if isinstance(ch, normParser.QueryExpressionContext):
                exprs.append(self.stack.pop())
        self.stack.append(list(reversed(exprs)))

    def exitQueryExpression(self, ctx:normParser.QueryExpressionContext):
        if ctx.DOT():
            eexpr = self.stack.pop() if ctx.evaluationExpression() else None
            variable_name = self.stack.pop() if ctx.variableName() else None
            qexpr = self.stack.pop()
            if variable_name:
                self.stack.append(PropertyExpr(qexpr, variable_name))
            elif eexpr:
                self.stack.append(ChainedEvaluationExpr(qexpr, eexpr))
            else:
                raise ParseError('Dot access only Property or functions. Something wrong with the expression')
            return
        if ctx.NT():
            qexpr = self.stack.pop()
            self.stack.append(CombinedExpr(LOP.NOT, qexpr, None))
            return
        if ctx.spacedLogicalOperator():
            expr2 = self.stack.pop()
            expr1 = self.stack.pop()
            lop = LOP(ctx.spacedLogicalOperator().logicalOperator().getText())
            self.stack.append(CombinedExpr(lop, expr1, expr2))

    def exitFullTypeDeclaration(self, ctx: normParser.FullTypeDeclarationContext):
        type_implementation = self.stack.pop()
        type_definition = self.stack.pop()
        self.stack.append(FullTypeDeclaration(type_definition, type_implementation))

    def exitIncrementalTypeDeclaration(self, ctx:normParser.IncrementalTypeDeclarationContext):
        type_implementation = self.stack.pop()
        type_name = self.stack.pop()
        self.stack.append(IncrementalTypeDeclaration(type_name, type_implementation))

    def exitTypeName(self, ctx:normParser.TypeNameContext):
        typename = ctx.TYPENAME()
        if typename:
            version = int(ctx.version().getText()[1:]) if ctx.version() else None
            self.stack.append(TypeName(str(typename), version))
        elif ctx.LSBR():
            self.stack.append(ListType(self.stack.pop()))
        elif ctx.OR():
            t1 = self.stack.pop()
            t2 = self.stack.pop()
            t = UnionType([])
            if isinstance(t2, UnionType):
                t.types.extend((tt for tt in t2.types if tt not in t))
            else:
                t.types.append(t2)
            if isinstance(t1, UnionType):
                t.types.extend((tt for tt in t1.types if tt not in t))
            else:
                t.types.append(t1)
            self.stack.append(t)
        else:
            raise ValueError('Not a valid type name definition')

    def exitVariableName(self, ctx:normParser.VariableNameContext):
        self.stack.append(VariableName(ctx.getText()))

    def exitArgumentDeclaration(self, ctx:normParser.ArgumentDeclarationContext):
        type_name = self.stack.pop()
        variable_name = self.stack.pop()
        self.stack.append(ArgumentDeclaration(variable_name, type_name))

    def exitArgumentDeclarations(self, ctx:normParser.ArgumentDeclarationsContext):
        arguments = []
        for arg in ctx.children:
            if isinstance(arg, normParser.ArgumentDeclarationContext):
                arguments.append(self.stack.pop())
        self.stack.append(list(reversed(arguments)))

    def exitTypeDefinition(self, ctx:normParser.TypeDefinitionContext):
        output_type_name = None
        argument_declarations = None
        if ctx.CL():
            output_type_name = self.stack.pop()
        if ctx.LBR():
            argument_declarations = self.stack.pop()
        type_name = self.stack.pop()
        self.stack.append(TypeDefinition(type_name, argument_declarations, output_type_name))

    def exitTypeImplementation(self, ctx:normParser.TypeImplementationContext):
        if ctx.LCBR():
            self.stack.append(TypeImpl(CodeMode.QUERY, ctx.code().getText()))
        elif ctx.PYTHON_BLOCK():
            self.stack.append(TypeImpl(CodeMode.PYTHON, ctx.code().getText()))
        elif ctx.KERAS_BLOCK():
            self.stack.append(TypeImpl(CodeMode.KERAS, ctx.code().getText()))
        else:
            raise ValueError('Only query, python, or keras code blocks are supported')

    def exitUpdateExpression(self, ctx:normParser.UpdateExpressionContext):
        query_result = self.stack.pop()
        # TODO update the query result to the database
        self.stack.append('Data {} for type {} have been updated at version {}')

    def exitDeleteExpression(self, ctx:normParser.DeleteExpressionContext):
        query_result = self.stack.pop()
        # TODO delete the query result from the database
        self.stack.append('Data {} for type {} have been deleted as version {}')

    def exitComment_contents(self, ctx: normParser.Comment_contentsContext):
        self.comments += ctx.getText()

    def exitComments(self, ctx: normParser.CommentsContext):
        content = ctx.getText()
        if content.startswith('//'):
            self.comments = content[2:]

    def exitNamespace(self, ctx: normParser.NamespaceContext):
        ns = ctx.namespace_name().getText()
        if ns:
            self.namespace = ns

    def exitImports(self, ctx: normParser.ImportsContext):
        ns = ctx.namespace_name().getText()
        if ns:
            self.imports.append(ns)
        tp = self.stack.pop() if ctx.typeName() else None
        if not tp:
            return
        als = ctx.TYPENAME().getText() if ctx.ALS() else tp.name
        self.alias[als] = tp

