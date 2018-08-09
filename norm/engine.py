from antlr4 import *
from collections import namedtuple
import re
from dateutil import parser as dateparser
from norm.normLexer import normLexer
from norm.normParser import normParser
from norm.normListener import normListener
from norm import config
from antlr4.error.ErrorListener import ErrorListener


class NormErrorListener(ErrorListener):

    def __init__(self):
        super(NormErrorListener, self).__init__()

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        err_msg = "line " + str(line) + ":" + str(column) + " " + msg
        raise ValueError(err_msg)


TypeName \
    = namedtuple('TypeName', ['name', 'version'])
ListType \
    = namedtuple('ListType', ['intern'])
UnionType \
    = namedtuple('UnionType', ['types'])
TypeDefinition \
    = namedtuple('TypeDefinition', ['type_name', 'argument_declarations', 'output_type_name'])
TypeImpl \
    = namedtuple('TypeImpl', ['mode', 'code'])
ArgumentDeclaration \
    = namedtuple('ArgumentDeclaration', ['variable_name', 'variable_type'])
ArgumentDeclarations \
    = namedtuple('ArgumentDeclarations', ['arguments'])
FullTypeDeclaration \
    = namedtuple('FullTypeDeclaration', ['namespace', 'type_definition', 'type_implementation'])
IncrementalTypeDeclaration \
    = namedtuple('IncrementalTypeDeclaration', ['type_name', 'type_implementation'])
Projection \
    = namedtuple('Projection', ['limit', 'variable_name'])
Constant \
    = namedtuple('Constant', ['type_name', 'value'])
BaseExpr \
    = namedtuple('BaseExpr', ['type_name', 'value'])
ListExpr \
    = namedtuple('ListExpr', ['elements'])
ArgumentExpr \
    = namedtuple('ArgumentExpr', ['expr', 'projection'])
EvaluationExpr \
    = namedtuple('EvaluationExpr', ['type_name', 'variable_name', 'args', 'projection'])
ArithmeticExpr \
    = namedtuple('ArithmeticExpr', ['op', 'expr1', 'expr2'])
AssignmentExpr \
    = namedtuple('AssignmentExpr', ['variable_name', 'expr'])
ConditionExpr \
    = namedtuple('ConditionExpr', ['aexpr', 'op', 'qexpr'])
CombinedExpr \
    = namedtuple('CombinedExpr', ['op', 'expr1', 'expr2'])
ConditionCombinedExpr \
    = namedtuple('ConditionCombinedExpr', ['op', 'expr1', 'expr2'])
PropertyExpr \
    = namedtuple('PropertyExpr', ['expr', 'property'])
ChainedEvaluationExpr \
    = namedtuple('ChainedEvaluationExpr', ['qexpr', 'eexpr'])


class ParseError(ValueError):
    pass


class NormSyntaxError(ValueError):
    pass


class NormExecutable(object):
    """
    Execute Norm Script
    """
    pass


class NormPlanner(object):
    """
    Optimize the execution plan for a given set of executables
    """
    pass


class NormCompiler(normListener):
    def __init__(self):
        self.comments = ''
        self.imports = []
        self.namespace = ''
        self.alias = {}
        self.variables = {}
        self.stack = []

    def exitNone(self, ctx:normParser.NoneContext):
        self.stack.append(Constant('none', None))

    def exitBool_c(self, ctx:normParser.Bool_cContext):
        self.stack.append(Constant('bool', ctx.getText().lower() == 'true'))

    def exitInteger_c(self, ctx:normParser.Integer_cContext):
        self.stack.append(Constant('int', int(ctx.getText())))

    def exitFloat_c(self, ctx:normParser.Float_cContext):
        self.stack.append(Constant('float', float(ctx.getText())))

    def exitString_c(self, ctx:normParser.String_cContext):
        self.stack.append(Constant('string', str(ctx.getText()[1:-1])))

    def exitUnicode_c(self, ctx:normParser.Unicode_cContext):
        self.stack.append(Constant('unicode', str(ctx.getText()[2:-1]).encode('utf-8', 'ignore')))

    def exitPattern(self, ctx:normParser.PatternContext):
        try:
            self.stack.append(Constant('pattern', re.compile(str(ctx.getText()[2:-1]))))
        except:
            raise ValueError('Pattern constant {} is in wrong format, should be Python regex pattern'
                             .format(ctx.getText()))

    def exitUuid(self, ctx:normParser.UuidContext):
        self.stack.append(Constant('uuid', str(ctx.getText()[2:-1])))

    def exitUrl(self, ctx:normParser.UrlContext):
        self.stack.append(Constant('url', str(ctx.getText()[2:-1])))

    def exitDatetime(self, ctx:normParser.DatetimeContext):
        self.stack.append(Constant('datetime', dateparser.parse(ctx.getText()[2:-1], fuzzy=True)))

    def exitBaseExpression(self, ctx:normParser.BaseExpressionContext):
        obj = self.stack.pop()
        if isinstance(obj, Constant):
            self.stack.append(BaseExpr('constant', obj))
        elif isinstance(obj, TypeName):
            self.stack.append(BaseExpr('type', obj))
        else:
            self.stack.append(BaseExpr('variable', obj))

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
        # TODO check whether it is a query expression
        self.stack.append(ArgumentExpr(expr, projection))

    def exitArgumentExpressions(self, ctx:normParser.ArgumentExpressionsContext):
        args = []
        for ch in ctx.children:
            if isinstance(ch, normParser.ArgumentExpressionContext):
                args.append(self.stack.pop())
        if not all([isinstance(arg, ArgumentExpr) for arg in args]):
            raise ParseError('Parsing Error, not all arguments parsed correctly')
        self.stack.append(ListExpr(list(reversed(args))))

    def exitEvaluationExpression(self, ctx:normParser.EvaluationExpressionContext):
        projection = self.stack.pop() if ctx.queryProjection() else None
        args = self.stack.pop() if ctx.argumentExpressions() else []
        variable_name = self.stack.pop() if ctx.variableName() else None
        type_name = self.stack.pop() if ctx.typeName() else None
        self.stack.append(EvaluationExpr(type_name, variable_name, args, projection))

    def exitArithmeticExpression(self, ctx:normParser.ArithmeticExpressionContext):
        if ctx.constant():
            if not isinstance(self.stack[-1], Constant):
                raise ParseError('It is supposed to be a constant not {}'.format(self.stack[-1]))
            if self.stack[-1].type_name not in {'int', 'float', 'bool'}:
                raise ValueError('Arithmetic can only work with numeric constant')
            return
        if ctx.variableName():
            # TODO check the variable to be numeric type
            return
        if ctx.listExpression():
            # TODO check the elements to be numeric type
            return
        if ctx.LBR():
            return
        if ctx.MINUS():
            expr = self.stack.pop()
            self.stack.append(ArithmeticExpr('-', expr, None))
            return
        if ctx.spacedArithmeticOperator():
            expr2 = self.stack.pop()
            expr1 = self.stack.pop()
            self.stack.append(ArithmeticExpr(ctx.spacedArithmeticOperator().arithmeticOperator().getText(),
                                             expr1, expr2))

    def exitAssignmentExpression(self, ctx:normParser.AssignmentExpressionContext):
        expr = self.stack.pop()
        variable_name = self.stack.pop()
        self.stack.append(AssignmentExpr(variable_name, expr))

    def exitConditionExpression(self, ctx:normParser.ConditionExpressionContext):
        qexpr = self.stack.pop()
        aexpr = self.stack.pop()
        self.stack.append(ConditionExpr(aexpr, ctx.spacedConditionOperator().conditionOperator().getText(),
                                        qexpr))

    def exitListExpression(self, ctx:normParser.ListExpressionContext):
        exprs = []
        for ch in ctx.children:
            if isinstance(ch, normParser.QueryExpressionContext):
                exprs.append(self.stack.pop())
        # TODO check element type to be expression
        self.stack.append(ListExpr(list(reversed(exprs))))

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
            if isinstance(qexpr, ConditionExpr) or isinstance(qexpr, ConditionCombinedExpr):
                self.stack.append(ConditionCombinedExpr('!', qexpr, None))
            else:
                self.stack.append(CombinedExpr('!', qexpr, None))
            return
        if ctx.spacedLogicalOperator():
            expr2 = self.stack.pop()
            expr1 = self.stack.pop()
            if (isinstance(expr1, ConditionExpr) or isinstance(expr1, ConditionCombinedExpr)) and\
                    (isinstance(expr2, ConditionExpr) or isinstance(expr2, ConditionCombinedExpr)):
                self.stack.append(ConditionCombinedExpr(ctx.spacedLogicalOperator().logicalOperator().getText(),
                                                        expr1, expr2))
            else:
                self.stack.append(CombinedExpr(ctx.spacedLogicalOperator().logicalOperator().getText(), expr1, expr2))

    def exitDeclarationExpression(self, ctx:normParser.DeclarationExpressionContext):
        type_declaration = self.stack.pop()
        if isinstance(type_declaration, FullTypeDeclaration):
            # TODO declare type
            pass
        elif isinstance(type_declaration, IncrementalTypeDeclaration):
            # TODO add on type
            pass
        else:
            raise ValueError('Wrong declaration syntax')

    def exitFullTypeDeclaration(self, ctx: normParser.FullTypeDeclarationContext):
        type_implementation = self.stack.pop()
        type_definition = self.stack.pop()
        self.stack.append(FullTypeDeclaration(self.namespace, type_definition, type_implementation))

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
            if isinstance(t1, UnionType):
                t.types.extend((tt for tt in t1.types if tt not in t))
            else:
                t.types.append(t1)
            if isinstance(t2, UnionType):
                t.types.extend((tt for tt in t2.types if tt not in t))
            else:
                t.types.append(t2)
            self.stack.append(t)
        else:
            raise ValueError('Not a valid type name definition')

    def exitVariableName(self, ctx:normParser.VariableNameContext):
        self.stack.append(ctx.getText())

    def exitArgumentDeclaration(self, ctx:normParser.ArgumentDeclarationContext):
        type_name = self.stack.pop()
        variable_name = self.stack.pop()
        self.stack.append(ArgumentDeclaration(variable_name, type_name))

    def exitArgumentDeclarations(self, ctx:normParser.ArgumentDeclarationsContext):
        arguments = []
        for arg in ctx.children:
            if isinstance(arg, normParser.ArgumentDeclarationContext):
                arguments.append(self.stack.pop())
        self.stack.append(ArgumentDeclarations(list(reversed(arguments))))

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
            self.stack.append(TypeImpl('query', ctx.code().getText()))
        elif ctx.PYTHON_BLOCK():
            self.stack.append(TypeImpl('python', ctx.code().getText()))
        elif ctx.KERAS_BLOCK():
            self.stack.append(TypeImpl('keras', ctx.code().getText()))
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

    def execute(self):
        pass


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


def compile_norm(script, last=True):
    """
    Compile the script
    :param script: the script to execute
    :type script: str
    :param last: compile the last statement, default to True
    :type last: bool
    :return: the executable
    :rtype: NormExecutable
    """
    script = script.strip(' \r\n\t')
    if last:
        script = trim_script(script)
    if script == '':
        return None

    lexer = normLexer(InputStream(script))
    stream = CommonTokenStream(lexer)
    parser = normParser(stream)
    parser.addErrorListener(NormErrorListener())
    tree = parser.script()
    compiler = NormCompiler()
    ParseTreeWalker().walk(compiler, tree)
    return compiler

