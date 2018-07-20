# Generated from /home/ax/Workspace/supernorm/norm/norm.g4 by ANTLR 4.7
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .normParser import normParser
else:
    from normParser import normParser

# This class defines a complete listener for a parse tree produced by normParser.
class normListener(ParseTreeListener):

    # Enter a parse tree produced by normParser#script.
    def enterScript(self, ctx:normParser.ScriptContext):
        pass

    # Exit a parse tree produced by normParser#script.
    def exitScript(self, ctx:normParser.ScriptContext):
        pass


    # Enter a parse tree produced by normParser#statement.
    def enterStatement(self, ctx:normParser.StatementContext):
        pass

    # Exit a parse tree produced by normParser#statement.
    def exitStatement(self, ctx:normParser.StatementContext):
        pass


    # Enter a parse tree produced by normParser#comments.
    def enterComments(self, ctx:normParser.CommentsContext):
        pass

    # Exit a parse tree produced by normParser#comments.
    def exitComments(self, ctx:normParser.CommentsContext):
        pass


    # Enter a parse tree produced by normParser#comment_contents.
    def enterComment_contents(self, ctx:normParser.Comment_contentsContext):
        pass

    # Exit a parse tree produced by normParser#comment_contents.
    def exitComment_contents(self, ctx:normParser.Comment_contentsContext):
        pass


    # Enter a parse tree produced by normParser#namespaceExpression.
    def enterNamespaceExpression(self, ctx:normParser.NamespaceExpressionContext):
        pass

    # Exit a parse tree produced by normParser#namespaceExpression.
    def exitNamespaceExpression(self, ctx:normParser.NamespaceExpressionContext):
        pass


    # Enter a parse tree produced by normParser#namespace_name.
    def enterNamespace_name(self, ctx:normParser.Namespace_nameContext):
        pass

    # Exit a parse tree produced by normParser#namespace_name.
    def exitNamespace_name(self, ctx:normParser.Namespace_nameContext):
        pass


    # Enter a parse tree produced by normParser#namespace.
    def enterNamespace(self, ctx:normParser.NamespaceContext):
        pass

    # Exit a parse tree produced by normParser#namespace.
    def exitNamespace(self, ctx:normParser.NamespaceContext):
        pass


    # Enter a parse tree produced by normParser#imports.
    def enterImports(self, ctx:normParser.ImportsContext):
        pass

    # Exit a parse tree produced by normParser#imports.
    def exitImports(self, ctx:normParser.ImportsContext):
        pass


    # Enter a parse tree produced by normParser#declarationExpression.
    def enterDeclarationExpression(self, ctx:normParser.DeclarationExpressionContext):
        pass

    # Exit a parse tree produced by normParser#declarationExpression.
    def exitDeclarationExpression(self, ctx:normParser.DeclarationExpressionContext):
        pass


    # Enter a parse tree produced by normParser#typeDefinition.
    def enterTypeDefinition(self, ctx:normParser.TypeDefinitionContext):
        pass

    # Exit a parse tree produced by normParser#typeDefinition.
    def exitTypeDefinition(self, ctx:normParser.TypeDefinitionContext):
        pass


    # Enter a parse tree produced by normParser#argumentDeclaration.
    def enterArgumentDeclaration(self, ctx:normParser.ArgumentDeclarationContext):
        pass

    # Exit a parse tree produced by normParser#argumentDeclaration.
    def exitArgumentDeclaration(self, ctx:normParser.ArgumentDeclarationContext):
        pass


    # Enter a parse tree produced by normParser#argumentDeclarations.
    def enterArgumentDeclarations(self, ctx:normParser.ArgumentDeclarationsContext):
        pass

    # Exit a parse tree produced by normParser#argumentDeclarations.
    def exitArgumentDeclarations(self, ctx:normParser.ArgumentDeclarationsContext):
        pass


    # Enter a parse tree produced by normParser#fullTypeDeclaration.
    def enterFullTypeDeclaration(self, ctx:normParser.FullTypeDeclarationContext):
        pass

    # Exit a parse tree produced by normParser#fullTypeDeclaration.
    def exitFullTypeDeclaration(self, ctx:normParser.FullTypeDeclarationContext):
        pass


    # Enter a parse tree produced by normParser#incrementalTypeDeclaration.
    def enterIncrementalTypeDeclaration(self, ctx:normParser.IncrementalTypeDeclarationContext):
        pass

    # Exit a parse tree produced by normParser#incrementalTypeDeclaration.
    def exitIncrementalTypeDeclaration(self, ctx:normParser.IncrementalTypeDeclarationContext):
        pass


    # Enter a parse tree produced by normParser#typeImplementation.
    def enterTypeImplementation(self, ctx:normParser.TypeImplementationContext):
        pass

    # Exit a parse tree produced by normParser#typeImplementation.
    def exitTypeImplementation(self, ctx:normParser.TypeImplementationContext):
        pass


    # Enter a parse tree produced by normParser#code.
    def enterCode(self, ctx:normParser.CodeContext):
        pass

    # Exit a parse tree produced by normParser#code.
    def exitCode(self, ctx:normParser.CodeContext):
        pass


    # Enter a parse tree produced by normParser#version.
    def enterVersion(self, ctx:normParser.VersionContext):
        pass

    # Exit a parse tree produced by normParser#version.
    def exitVersion(self, ctx:normParser.VersionContext):
        pass


    # Enter a parse tree produced by normParser#typeName.
    def enterTypeName(self, ctx:normParser.TypeNameContext):
        pass

    # Exit a parse tree produced by normParser#typeName.
    def exitTypeName(self, ctx:normParser.TypeNameContext):
        pass


    # Enter a parse tree produced by normParser#variableName.
    def enterVariableName(self, ctx:normParser.VariableNameContext):
        pass

    # Exit a parse tree produced by normParser#variableName.
    def exitVariableName(self, ctx:normParser.VariableNameContext):
        pass


    # Enter a parse tree produced by normParser#querySign.
    def enterQuerySign(self, ctx:normParser.QuerySignContext):
        pass

    # Exit a parse tree produced by normParser#querySign.
    def exitQuerySign(self, ctx:normParser.QuerySignContext):
        pass


    # Enter a parse tree produced by normParser#queryLimit.
    def enterQueryLimit(self, ctx:normParser.QueryLimitContext):
        pass

    # Exit a parse tree produced by normParser#queryLimit.
    def exitQueryLimit(self, ctx:normParser.QueryLimitContext):
        pass


    # Enter a parse tree produced by normParser#queryProjection.
    def enterQueryProjection(self, ctx:normParser.QueryProjectionContext):
        pass

    # Exit a parse tree produced by normParser#queryProjection.
    def exitQueryProjection(self, ctx:normParser.QueryProjectionContext):
        pass


    # Enter a parse tree produced by normParser#argumentExpressions.
    def enterArgumentExpressions(self, ctx:normParser.ArgumentExpressionsContext):
        pass

    # Exit a parse tree produced by normParser#argumentExpressions.
    def exitArgumentExpressions(self, ctx:normParser.ArgumentExpressionsContext):
        pass


    # Enter a parse tree produced by normParser#argumentExpression.
    def enterArgumentExpression(self, ctx:normParser.ArgumentExpressionContext):
        pass

    # Exit a parse tree produced by normParser#argumentExpression.
    def exitArgumentExpression(self, ctx:normParser.ArgumentExpressionContext):
        pass


    # Enter a parse tree produced by normParser#updateExpression.
    def enterUpdateExpression(self, ctx:normParser.UpdateExpressionContext):
        pass

    # Exit a parse tree produced by normParser#updateExpression.
    def exitUpdateExpression(self, ctx:normParser.UpdateExpressionContext):
        pass


    # Enter a parse tree produced by normParser#deleteExpression.
    def enterDeleteExpression(self, ctx:normParser.DeleteExpressionContext):
        pass

    # Exit a parse tree produced by normParser#deleteExpression.
    def exitDeleteExpression(self, ctx:normParser.DeleteExpressionContext):
        pass


    # Enter a parse tree produced by normParser#queryExpression.
    def enterQueryExpression(self, ctx:normParser.QueryExpressionContext):
        pass

    # Exit a parse tree produced by normParser#queryExpression.
    def exitQueryExpression(self, ctx:normParser.QueryExpressionContext):
        pass


    # Enter a parse tree produced by normParser#baseExpression.
    def enterBaseExpression(self, ctx:normParser.BaseExpressionContext):
        pass

    # Exit a parse tree produced by normParser#baseExpression.
    def exitBaseExpression(self, ctx:normParser.BaseExpressionContext):
        pass


    # Enter a parse tree produced by normParser#listExpression.
    def enterListExpression(self, ctx:normParser.ListExpressionContext):
        pass

    # Exit a parse tree produced by normParser#listExpression.
    def exitListExpression(self, ctx:normParser.ListExpressionContext):
        pass


    # Enter a parse tree produced by normParser#evaluationExpression.
    def enterEvaluationExpression(self, ctx:normParser.EvaluationExpressionContext):
        pass

    # Exit a parse tree produced by normParser#evaluationExpression.
    def exitEvaluationExpression(self, ctx:normParser.EvaluationExpressionContext):
        pass


    # Enter a parse tree produced by normParser#arithmeticExpression.
    def enterArithmeticExpression(self, ctx:normParser.ArithmeticExpressionContext):
        pass

    # Exit a parse tree produced by normParser#arithmeticExpression.
    def exitArithmeticExpression(self, ctx:normParser.ArithmeticExpressionContext):
        pass


    # Enter a parse tree produced by normParser#assignmentExpression.
    def enterAssignmentExpression(self, ctx:normParser.AssignmentExpressionContext):
        pass

    # Exit a parse tree produced by normParser#assignmentExpression.
    def exitAssignmentExpression(self, ctx:normParser.AssignmentExpressionContext):
        pass


    # Enter a parse tree produced by normParser#conditionExpression.
    def enterConditionExpression(self, ctx:normParser.ConditionExpressionContext):
        pass

    # Exit a parse tree produced by normParser#conditionExpression.
    def exitConditionExpression(self, ctx:normParser.ConditionExpressionContext):
        pass


    # Enter a parse tree produced by normParser#nativeProperty.
    def enterNativeProperty(self, ctx:normParser.NativePropertyContext):
        pass

    # Exit a parse tree produced by normParser#nativeProperty.
    def exitNativeProperty(self, ctx:normParser.NativePropertyContext):
        pass


    # Enter a parse tree produced by normParser#aggregationFunction.
    def enterAggregationFunction(self, ctx:normParser.AggregationFunctionContext):
        pass

    # Exit a parse tree produced by normParser#aggregationFunction.
    def exitAggregationFunction(self, ctx:normParser.AggregationFunctionContext):
        pass


    # Enter a parse tree produced by normParser#none.
    def enterNone(self, ctx:normParser.NoneContext):
        pass

    # Exit a parse tree produced by normParser#none.
    def exitNone(self, ctx:normParser.NoneContext):
        pass


    # Enter a parse tree produced by normParser#constant.
    def enterConstant(self, ctx:normParser.ConstantContext):
        pass

    # Exit a parse tree produced by normParser#constant.
    def exitConstant(self, ctx:normParser.ConstantContext):
        pass


    # Enter a parse tree produced by normParser#logicalOperator.
    def enterLogicalOperator(self, ctx:normParser.LogicalOperatorContext):
        pass

    # Exit a parse tree produced by normParser#logicalOperator.
    def exitLogicalOperator(self, ctx:normParser.LogicalOperatorContext):
        pass


    # Enter a parse tree produced by normParser#spacedLogicalOperator.
    def enterSpacedLogicalOperator(self, ctx:normParser.SpacedLogicalOperatorContext):
        pass

    # Exit a parse tree produced by normParser#spacedLogicalOperator.
    def exitSpacedLogicalOperator(self, ctx:normParser.SpacedLogicalOperatorContext):
        pass


    # Enter a parse tree produced by normParser#conditionOperator.
    def enterConditionOperator(self, ctx:normParser.ConditionOperatorContext):
        pass

    # Exit a parse tree produced by normParser#conditionOperator.
    def exitConditionOperator(self, ctx:normParser.ConditionOperatorContext):
        pass


    # Enter a parse tree produced by normParser#spacedConditionOperator.
    def enterSpacedConditionOperator(self, ctx:normParser.SpacedConditionOperatorContext):
        pass

    # Exit a parse tree produced by normParser#spacedConditionOperator.
    def exitSpacedConditionOperator(self, ctx:normParser.SpacedConditionOperatorContext):
        pass


    # Enter a parse tree produced by normParser#arithmeticOperator.
    def enterArithmeticOperator(self, ctx:normParser.ArithmeticOperatorContext):
        pass

    # Exit a parse tree produced by normParser#arithmeticOperator.
    def exitArithmeticOperator(self, ctx:normParser.ArithmeticOperatorContext):
        pass


    # Enter a parse tree produced by normParser#spacedArithmeticOperator.
    def enterSpacedArithmeticOperator(self, ctx:normParser.SpacedArithmeticOperatorContext):
        pass

    # Exit a parse tree produced by normParser#spacedArithmeticOperator.
    def exitSpacedArithmeticOperator(self, ctx:normParser.SpacedArithmeticOperatorContext):
        pass


