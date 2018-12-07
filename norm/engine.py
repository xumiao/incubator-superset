import re

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from dateutil import parser as dateparser
from functools import lru_cache
from textwrap import dedent

from norm import config
from norm.executable import Constant, Projection, NormExecutable
from norm.executable.declaration import *
from norm.executable.expression.arithmetic import *
from norm.executable.expression.code import *
from norm.executable.expression.condition import *
from norm.executable.expression.evaluation import *
from norm.executable.expression.query import *
from norm.executable.expression.slice import *
from norm.executable.implementation import *
from norm.executable.type import *
from norm.executable.namespace import *
from norm.literals import AOP, COP, LOP, ImplType, CodeMode, ConstantType, OMMIT
from norm.utils import current_user
from norm.normLexer import normLexer
from norm.normListener import normListener
from norm.normParser import normParser


class ParseError(ValueError):
    pass


class NormErrorListener(ErrorListener):

    def __init__(self):
        super(NormErrorListener, self).__init__()

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        err_msg = "line " + str(line) + ":" + str(column) + " " + msg
        raise ValueError(err_msg)


walker = ParseTreeWalker()


class NormCompiler(normListener):

    def __init__(self, context_id):
        # TODO: make sure the context can be save/load from cache
        # context_id, namespaces should be able to be saved directly
        # variable, stack and df should be reset
        self.context_id = context_id
        self.user = current_user()
        self.context_namespace = '{}.{}'.format(config.CONTEXT_NAMESPACE_STUB, context_id)
        self.user_namespace = '{}.{}'.format(config.USER_NAMESPACE_STUB, self.user.username)
        from norm.models.native import NativeLambda
        self.search_namespaces = {NativeLambda.NAMESPACE, self.context_namespace, self.user_namespace}
        self.stack = []
        self.df = None
        self.session = None

    def set_session(self, session):
        self.session = session
        self.stack = []
        self.df = None

    def optimize(self):
        """
        Optimize the AST to have a more efficient execution plan
        # TODO
        * Filtering conditions can be combined and executed in batch instead of sequential
        * Arithmetic equations can be combined and passed to DF in batch instead of sequential
        """
        pass

    def compile(self, script):
        if script is None or not isinstance(script, str):
            return None
        script = script.strip(' \r\n\t')
        if script == '':
            return None

        lexer = normLexer(InputStream(script))
        stream = CommonTokenStream(lexer)
        parser = normParser(stream)
        parser.addErrorListener(NormErrorListener())
        tree = parser.script()
        walker.walk(self, tree)
        self.optimize()
        return self.stack.pop()

    def execute(self, script):
        exe = self.compile(dedent(script))
        if isinstance(exe, NormExecutable):
            return exe.execute(self.session, self)
        else:
            return exe

    def exitStatement(self, ctx:normParser.StatementContext):
        if ctx.imports():
            # pass up
            pass
        elif ctx.exports():
            # pass up
            pass
        elif ctx.typeDeclaration():
            type_declaration = self.stack.pop()
            description = self.stack.pop() if ctx.comments() else ''
            type_declaration.description = description
            self.stack.append(type_declaration)
        elif ctx.queryExpression():
            query = self.stack.pop()
            description = self.stack.pop() if ctx.comments() else ''
            if ctx.typeName():
                if ctx.OR():
                    op = ImplType.ORAS
                elif ctx.AND():
                    op = ImplType.ANDAS
                else:
                    op = ImplType.ASS
                type_name = self.stack.pop()
                self.stack.append(TypeImplementation(type_name, op, query, description))
            else:
                self.stack.append(query)
        else:
            # nothing to be parsed
            pass

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
            raise ParseError('Pattern constant {} is in wrong format, should be Python regex pattern'
                             .format(ctx.getText()))

    def exitUuid(self, ctx:normParser.UuidContext):
        self.stack.append(Constant(ConstantType.UID, str(ctx.getText()[2:-1])))

    def exitUrl(self, ctx:normParser.UrlContext):
        self.stack.append(Constant(ConstantType.URL, str(ctx.getText()[2:-1])))

    def exitDatetime(self, ctx:normParser.DatetimeContext):
        self.stack.append(Constant(ConstantType.DTM, dateparser.parse(ctx.getText()[2:-1], fuzzy=True)))

    def exitQueryLimit(self, ctx:normParser.QueryLimitContext):
        lmt = ctx.getText()
        try:
            lmt = int(lmt)
            if lmt < 0:
                raise ParseError('Query limit must be positive integer, but we get {}'.format(lmt))
        except:
            raise ParseError('Query limit must be positive integer, but we get {}'.format(lmt))
        self.stack.append(lmt)

    def exitQueryProjection(self, ctx:normParser.QueryProjectionContext):
        variable = self.stack.pop() if ctx.variableName() else None
        lmt = self.stack.pop() if ctx.queryLimit() else None
        self.stack.append(Projection(lmt, variable))

    def exitComments(self, ctx:normParser.CommentsContext):
        spaces = ' \r\n\t'
        cmt = ctx.getText()
        if ctx.MULTILINE():
            cmt = cmt.strip(spaces)[2:-2].strip(spaces)
        elif ctx.SINGLELINE():
            cmt = cmt.strip(spaces)[2:].strip(spaces)
        self.stack.append(cmt)

    def exitImports(self, ctx:normParser.ImportsContext):
        type_ = self.stack.pop() if ctx.typeName() else None
        namespace = [str(v) for v in ctx.VARNAME()]
        variable = namespace.pop() if ctx.AS() else None
        self.stack.append(Import('.'.join(namespace), type_, variable))

    def exitExports(self, ctx:normParser.ExportsContext):
        type_ = self.stack.pop()
        namespace = [str(v) for v in ctx.VARNAME()]
        variable = namespace.pop() if ctx.AS() else None
        self.stack.append(Export('.'.join(namespace), type_, variable))

    def exitArgumentDeclaration(self, ctx:normParser.ArgumentDeclarationContext):
        if ctx.OMMIT():
            self.stack.append(ArgumentDeclaration(OMMIT, None))
        else:
            type_name = self.stack.pop()
            variable_name = self.stack.pop()
            self.stack.append(ArgumentDeclaration(variable_name, type_name))

    def exitArgumentDeclarations(self, ctx:normParser.ArgumentDeclarationsContext):
        args = reversed([self.stack.pop() for ch in ctx.children
                         if isinstance(ch, normParser.ArgumentDeclarationContext)])
        self.stack.append(list(args))

    def exitTypeDeclaration(self, ctx:normParser.TypeDeclarationContext):
        output_type_name = self.stack.pop() if ctx.typeName(1) else None
        args = self.stack.pop() if ctx.argumentDeclarations() else None
        type_name = self.stack.pop()
        self.stack.append(TypeDeclaration(type_name, args, output_type_name))

    def exitTypeName(self, ctx:normParser.TypeNameContext):
        typename = ctx.VARNAME()
        if typename:
            version = int(ctx.version().getText()[1:]) if ctx.version() else None
            self.stack.append(TypeName(str(typename), version))
        elif ctx.LSBR():
            self.stack.append(ListType(self.stack.pop()))
        else:
            raise ParseError('Not a valid type name definition')

    def exitVariableName(self, ctx:normParser.VariableNameContext):
        attribute = ctx.VARNAME().getText()
        variable = self.stack.pop() if ctx.variableName() else None
        if variable is not None:
            self.stack.append(VariableName(variable, attribute))
        else:
            self.stack.append(VariableName(attribute))

    def exitArgumentExpression(self, ctx:normParser.ArgumentExpressionContext):
        var = None
        expr = None
        projection = None
        if ctx.OMMIT():
            var = OMMIT
        elif ctx.arithmeticExpression():
            expr = self.stack.pop()
            var = self.stack.pop() if ctx.variableName() else None
        elif ctx.variableName() and ctx.queryProjection():
            projection = self.stack.pop()
            var = self.stack.pop()
        elif ctx.conditionExpression():
            projection = self.stack.pop() if ctx.queryProjection() else None
            expr = self.stack.pop()
        elif ctx.queryProjection():
            projection = self.stack.pop()
        self.stack.append(ArgumentExpr(var, expr, projection))

    def exitArgumentExpressions(self, ctx:normParser.ArgumentExpressionsContext):
        args = [self.stack.pop() for ch in ctx.children
                if isinstance(ch, normParser.ArgumentExpressionContext)]
        self.stack.append(args)

    def exitBaseQueryExpression(self, ctx:normParser.BaseQueryExpressionContext):
        pass

    def exitQueryExpression(self, ctx:normParser.QueryExpressionContext):
        projection = self.stack.pop() if ctx.queryProjection() else None
        expr2 = self.stack.pop() if ctx.spacedLogicalOperator() else None
        expr1 = self.stack.pop()
        op = None
        if ctx.NT():
            op = LOP.NOT
        elif ctx.spacedLogicalOperator():
            op = LOP(ctx.spacedLogicalOperator().logicalOperator().getText())
        self.stack.append(QueryExpr(op, expr1, expr2, projection))

    def exitEvaluationExpression(self, ctx:normParser.EvaluationExpressionContext):
        args = self.stack.pop() if ctx.argumentExpressions() else []
        type_name = self.stack.pop() if ctx.typeName() else None
        if type_name is None:
            raise ParseError('Evaluation expression at least starts with a type or a variable')
        self.stack.append(EvaluationExpr(type_name, args))

    def exitArithmeticExpression(self, ctx:normParser.ArithmeticExpressionContext):
        if ctx.LBR():
            return
        constant = self.stack.pop() if ctx.constant() else None
        variable = self.stack.pop() if ctx.variableName() else None
        if ctx.MINUS():
            expr = self.stack.pop()
            self.stack.append(ArithmeticExpr(constant, variable, AOP.SUB, expr))
            return
        if ctx.spacedArithmeticOperator():
            expr2 = self.stack.pop()
            expr1 = self.stack.pop()
            aop = AOP(ctx.spacedArithmeticOperator().arithmeticOperator().getText())
            self.stack.append(ArithmeticExpr(constant, variable, aop, expr1, expr2))

    def exitConditionExpression(self, ctx:normParser.ConditionExpressionContext):
        qexpr = self.stack.pop() if ctx.arithmeticExpression(1) else None
        aexpr = self.stack.pop()
        cop = COP(ctx.spacedConditionOperator().conditionOperator().getText()) \
            if ctx.spacedConditionOperator() else None
        self.stack.append(ConditionExpr(cop, aexpr, qexpr))

    def exitSliceExpression(self, ctx:normParser.SliceExpressionContext):
        end = self.stack.pop().value if ctx.integer_c(1) else None
        start = self.stack.pop().value if ctx.integer_c(0) else None
        expr = self.stack.pop()
        self.stack.append(SliceExpr(expr, start, end))

    def exitChainedExpression(self, ctx:normParser.ChainedExpressionContext):
        eexpr = self.stack.pop()
        qexpr = self.stack.pop()
        self.stack.append(ChainedEvaluationExpr(qexpr, eexpr))

    def exitCodeExpression(self, ctx:normParser.CodeExpressionContext):
        if ctx.KERAS_BLOCK():
            self.stack.append(CodeExpr(CodeMode.KERAS, ctx.code().getText()))
        elif ctx.PYTHON_BLOCK():
            self.stack.append(CodeExpr(CodeMode.PYTHON, ctx.code().getText()))
        elif ctx.SQL_BLOCK():
            self.stack.append(CodeExpr(CodeMode.SQL, ctx.code().getText()))
        else:
            self.stack.append(CodeExpr(CodeMode.QUERY, ctx.code().getText()))


@lru_cache(maxsize=128)
def get_compiler(context_id):
    """
    Get the compiler with respect to the context id
    :param context_id: the id for the context
    :type context_id: int
    :return: a norm compiler
    :rtype: NormCompiler
    """
    return NormCompiler(context_id)


def executor(context_id, session):
    compiler = get_compiler(context_id)
    compiler.set_session(session)
    return compiler
