import re

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from dateutil import parser as dateparser
from functools import lru_cache
from textwrap import dedent

from norm import config
from norm.executable import Constant, Projection, NormExecutable, ListConstant
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
from norm.literals import AOP, COP, LOP, ImplType, CodeMode, ConstantType
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
        # context_id, user, namespaces should be able to be cached directly
        # scope, stack and session should be reset
        self.context_id = context_id
        self.scope = None
        self.stack = []
        self.session = None
        self.user = None
        self.context_namespace = None
        self.user_namespace = None
        self.search_namespaces = None
        self.set_namespaces()

    def set_namespaces(self):
        self.user = current_user()
        self.context_namespace = '{}.{}'.format(config.CONTEXT_NAMESPACE_STUB, self.context_id)
        self.user_namespace = '{}.{}'.format(config.USER_NAMESPACE_STUB, self.user.username)
        from norm.models import NativeLambda
        self.search_namespaces = {NativeLambda.NAMESPACE, self.context_namespace, self.user_namespace}

    def set_session(self, session):
        """
        Set the db session
        :param session: the db session
        :type session: sqlalchemy.session
        """
        self.session = session
        self.scope = None
        self.stack = []

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
        assert(len(self.stack) == 1)  # Ensure that parsing has finished completely
        exe = self.stack.pop()
        exe.compile(self)
        return exe

    def execute(self, script):
        exe = self.compile(dedent(script))
        if isinstance(exe, NormExecutable):
            return exe.execute(self)
        else:
            # TODO: shouldn't be here
            return exe

    def exitStatement(self, ctx:normParser.StatementContext):
        if ctx.typeDeclaration():
            type_declaration = self.stack.pop()
            description = self.stack.pop() if ctx.comments() else ''
            type_declaration.description = description
            self.stack.append(type_declaration)
        elif ctx.typeName():
            query = self.stack.pop()
            type_name = self.stack.pop()
            description = self.stack.pop() if ctx.comments() else ''
            if ctx.OR():
                op = ImplType.OR_DEF
            elif ctx.AND():
                op = ImplType.AND_DEF
            elif ctx.COLON():
                op = ImplType.DEF
            else:
                msg = 'Currently only support :=, |=, &= for implementation'
                logger.error(msg)
                raise NormError(msg)
            self.stack.append(TypeImplementation(type_name, op, query, description))
        elif ctx.imports() or ctx.exports() or ctx.multiLineExpression():
            expr = self.stack.pop()
            # ignore comments
            self.stack.pop()
            self.stack.append(expr)

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

    def exitConstant(self, ctx:normParser.ConstantContext):
        if ctx.LSBR():
            constants = reversed([self.stack.pop() for ch in ctx.children
                                  if isinstance(ch, normParser.ConstantContext)])
            value = [constant.value for constant in constants]
            types = set(constant.type_ for constant in constants)
            if len(types) > 1:
                type_ = ConstantType.ANY
            else:
                type_ = types.pop()
            self.stack.append(ListConstant(type_, value))

    def exitQueryProjection(self, ctx:normParser.QueryProjectionContext):
        variables = reversed([self.stack.pop() for ch in ctx.children
                              if isinstance(ch, normParser.VariableContext)])
        to_evaluate = True if ctx.LCBR() else False
        self.stack.append(Projection(variables, to_evaluate))

    def exitComments(self, ctx:normParser.CommentsContext):
        spaces = ' \r\n\t'
        cmt = ctx.getText()
        if ctx.MULTILINE():
            cmt = cmt.strip(spaces)[2:-2].strip(spaces)
        elif ctx.SINGLELINE():
            cmt = '\n'.join(cmt_line.strip(spaces)[2:].strip(spaces) for cmt_line in cmt.split('\n'))
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

    def exitVariable(self, ctx:normParser.VariableContext):
        variable = ctx.VARNAME().getText()
        attribute = self.stack.pop() if ctx.variable() else None
        self.stack.append(VariableName(variable, attribute))

    def exitArgumentExpression(self, ctx:normParser.ArgumentExpressionContext):
        projection = self.stack.pop() if ctx.queryProjection() else None
        expr = self.stack.pop() if ctx.arithmeticExpression() else None
        op = COP(ctx.spacedConditionOperator().conditionOperator().getText().lower()) \
            if ctx.spacedConditionOperator() else None
        variable = self.stack.pop() if ctx.variable() else None
        self.stack.append(ArgumentExpr(variable, op, expr, projection))

    def exitArgumentExpressions(self, ctx:normParser.ArgumentExpressionsContext):
        args = [self.stack.pop() for ch in ctx.children
                if isinstance(ch, normParser.ArgumentExpressionContext)]
        self.stack.append(args)

    def exitMultiLineExpression(self, ctx:normParser.MultiLineExpressionContext):
        if ctx.newlineLogicalOperator():
            expr2 = self.stack.pop()
            expr1 = self.stack.pop()
            op = LOP(ctx.newlineLogicalOperator().logicalOperator().getText())
            self.stack.append(QueryExpr(op, expr1, expr2))

    def exitOneLineExpression(self, ctx:normParser.OneLineExpressionContext):
        if ctx.queryProjection():
            projection = self.stack.pop()
            expr = self.stack.pop()
            self.stack.append(ProjectedQueryExpr(expr, projection))
        elif ctx.NOT():
            expr = self.stack.pop()
            self.stack.append(NegatedQueryExpr(expr))
        elif ctx.spacedLogicalOperator():
            expr2 = self.stack.pop()
            expr1 = self.stack.pop()
            op = LOP(ctx.spacedLogicalOperator().logicalOperator().getText())
            self.stack.append(QueryExpr(op, expr1, expr2))

    def exitConditionExpression(self, ctx:normParser.ConditionExpressionContext):
        if ctx.spacedConditionOperator():
            qexpr = self.stack.pop()
            aexpr = self.stack.pop()
            cop = COP(ctx.spacedConditionOperator().conditionOperator().getText().lower())
            self.stack.append(ConditionExpr(cop, aexpr, qexpr))

    def exitArithmeticExpression(self, ctx:normParser.ArithmeticExpressionContext):
        if ctx.slicedExpression():
            return

        expr2 = self.stack.pop()
        op = None
        if ctx.MOD():
            op = AOP.MOD
        elif ctx.EXP():
            op = AOP.EXP
        elif ctx.TIMES():
            op = AOP.MUL
        elif ctx.DIVIDE():
            op = AOP.DIV
        elif ctx.PLUS():
            op = AOP.ADD
        elif ctx.MINUS():
            op = AOP.SUB
        expr1 = self.stack.pop() if ctx.arithmeticExpression(1) else None
        self.stack.append(ArithmeticExpr(op, expr1, expr2))

    def exitSlicedExpression(self, ctx:normParser.SlicedExpressionContext):
        if ctx.LSBR():
            if ctx.evaluationExpression(1):
                expr_range = self.stack.pop()
                expr = self.stack.pop()
                self.stack.append(EvaluatedSliceExpr(expr, expr_range))
            else:
                end = self.stack.pop().value if ctx.integer_c(1) else None
                start = self.stack.pop().value if ctx.integer_c(0) else None
                expr = self.stack.pop()
                self.stack.append(SliceExpr(expr, start, end))

    def exitEvaluationExpression(self, ctx:normParser.EvaluationExpressionContext):
        if ctx.DOT():
            rexpr = self.stack.pop()
            lexpr = self.stack.pop()
            self.stack.append(ChainedEvaluationExpr(lexpr, rexpr))
        elif ctx.argumentExpressions():
            args = self.stack.pop()
            variable = self.stack.pop()
            self.stack.append(EvaluationExpr(variable, args))

    def exitCodeExpression(self, ctx:normParser.CodeExpressionContext):
        if ctx.PYTHON_BLOCK():
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
