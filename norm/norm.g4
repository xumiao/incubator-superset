grammar norm;

script
    : statement (WSS* statement)* WSS*
    ;

statement
    : comments
    | namespaceExpression WSS* SEMICOLON
    | typeDeclaration WSS* SEMICOLON
    | updateExpression WSS* SEMICOLON
    | queryExpression WSS* SEMICOLON
    | deleteExpression WSS* SEMICOLON
    ;

COMMENT
    : '//' ~[\r\n]* -> skip
    ;

comments
    : '/*' comment_contents '*/'
    | COMMENT
    ;

comment_contents
    : ~('*/')*?
    ;

namespaceExpression
    : namespace WSS*
    | imports WSS*
    ;
namespace_name: VARNAME (DOT VARNAME)*;

namespace: SPACED_NAMESPACE namespace_name;

SPACED_NAMESPACE: 'namespace' [ \t]*;

imports: SPACED_IMPORT namespace_name;

SPACED_IMPORT: 'import' [ \t]*;


typeDeclaration
    : anonymousTypeDeclaration
    | fullTypeDeclaration
    | incrementalTypeDeclaration
    ;

anonymousTypeDeclaration
    : LCBR queryExpression RCBR
    | LBR  RBR CL typeExpression AS LCBR queryExpression RCBR
    | LBR argumentDeclarations RBR (CL typeExpression)* AS LCBR queryExpression RCBR
    ;

typeDefinition
    : typeName LBR RBR CL typeExpression
    | typeName LBR argumentDeclarations RBR (CL typeExpression)*
    ;

fullTypeDeclaration : typeDefinition AS typeImplementation;

incrementalTypeDeclaration
    : typeName ORAS typeImplementation
    ;

ORAS : [ \t\u000C]* OR '=' [ \t\u000C\r\n]*;


typeImplementation
    : queryExpression
    | LCBR queryExpression* RCBR
    | kerasImplementation
    | pythonImplementation
    ;

kerasImplementation
    : '{%keras' code '%}'
    ;

pythonImplementation
    : '{%python' code '%}'
    ;

code
    : ~('%}')*?
    ;

argumentDeclaration
    : typeExpression
    | variableName CL typeExpression
    ;

argumentDeclarations: argumentDeclaration (CA argumentDeclaration)*;

version
    : '@' INTEGER
    | '@' INTEGER DOT UUID
    ;

typeName : TYPENAME | TYPENAME version;
variableName : VARNAME | nativeProperty;

typeExpression
    : typeName
    | typeName LCBR argumentExpressions RCBR
    ;

typeEvaluation
    : typeExpression LBR RBR
    | typeExpression LBR argumentExpressions RBR
    | typeExpression LBR argumentExpressions RBR queryTerm
    | variableName LBR RBR
    | variableName LBR argumentExpressions RBR
    | variableName LBR argumentExpressions RBR queryTerm
    ;

querySign: '?' | '?' queryLimit | '?*';

queryTerm
    : querySign
    | querySign variableName (DOT variableName)*
    ;

queryLimit : INTEGER;

queryConstraints
    : queryContraint (spacedLogicalOperator queryContraint)*
    | LBR queryConstraints RBR
    ;

queryContraint: variableName spacedConstraintOperator queryExpression;


argumentExpressions : argumentExpression (CA argumentExpression)*;

argumentExpression
    : argumentAssignmentExpression
    | constraintExpression
    ;

argumentAssignmentExpression
    : assignmentExpression
    | queryExpression
    ;

constraintExpression
    : queryConstraints
    | LBR queryConstraints RBR queryTerm
    | queryTerm
    ;

updateExpression
    : queryExpression DOT propertyAggregation AS queryExpression
    | typeName LBR RBR DOT
    | typeName LBR argumentAssignmentExpression (CA argumentAssignmentExpression)* RBR DOT
    ;

SPACED_DELETE: 'del' [ \t]* | 'delete' [\t]*;

deleteExpression: SPACED_DELETE queryExpression;

queryExpression
    : baseExpression
    | embracedExpression
    | queryExpression WSS* DOT WSS* propertyAggregation
    | listExpression
    | assignmentExpression
    | NT queryExpression
    | queryExpression spacedLogicalOperator queryExpression
    ;

baseExpression
    : constant
    | variableName
    | typeEvaluation
    | typeExpression
    ;

embracedExpression : LBR queryExpression RBR;

listExpression : LSBR queryExpression (CA queryExpression)* RSBR;

assignmentExpression : variableName AS queryExpression;

nativeProperty: 'prob' | 'label' | 'tag' | 'uid' | 'tensor' | 'timestamp' | 'version';

propertyAggregation : nativeProperty | variableName | aggregationEvaluation;

aggregationFunction : 'max' | 'min' | 'ave' | 'count' | 'group' | 'unique' | 'sort' | 'sample';

aggregationEvaluation
    : aggregationFunction LBR RBR
    | aggregationFunction LBR aggregationArgumentExpressions RBR
    ;

aggregationArgumentExpression
    : variableName AS constant
    | variableName AS variableName
    | variableName AS aggregationFunction
    ;

aggregationArgumentExpressions
    : aggregationArgumentExpression (CA aggregationArgumentExpression)*
    ;

none: 'none' | 'null' | 'na';

constant
    : none
    | BOOLEAN
    | INTEGER
    | FLOAT
    | STRING
    | UNICODE
    | PATTERN
    | UUID
    | URL
    | DATETIME
    ;

WSS: [ \t\u000C\r\n]+;

LBR: '(' [ \t\u000C\r\n]*;
RBR: [ \t\u000C\r\n]* ')';

LCBR: '{' [ \t\u000C\r\n]*;
RCBR: [ \t\u000C\r\n]* '}';

LSBR: '[' [ \t\u000C\r\n]*;
RSBR: [ \t\u000C\r\n]* ']';

NT: NOT [ \t]*;

CA: [ \t\u000C\r\n]* COMMA [ \t\u000C\r\n]*;

CL: [ \t\u000C\r\n]* COLON [ \t\u000C\r\n]*;

AS: [ \t\u000C\r\n]* '=' [ \t\u000C\r\n]*;

logicalOperator: AND | OR | XOR | IMP | EQV;

spacedLogicalOperator
    : logicalOperator
    | logicalOperator WSS
    | WSS logicalOperator
    | WSS logicalOperator WSS
    ;

constraintOperator: EQ | NE | IN | NIN | LT | LE | GT | GE | LIKE;

spacedConstraintOperator
    : constraintOperator
    | constraintOperator WSS
    | WSS constraintOperator
    | WSS constraintOperator WSS
    ;

arithmeticOperator: PLUS | MINUS | TIMES | DIVIDE | MOD;

spacedArithmeticOperator
    : arithmeticOperator
    | arithmeticOperator WSS
    | WSS arithmeticOperator
    | WSS arithmeticOperator WSS
    ;

IN:        'in';
NIN:       '!in';
AND:       '&' | '&&';
COLON:     ':';
COMMA:     ',';
DIVIDE:    '/';
DOT:       '.';
DOTDOT:    '..';
EQ:        '==';
GE:        '>=';
GT:        '>';
LE:        '<=';
LT:        '<';
MINUS:     '-';
MOD:       '%';
NOT:       '!';
NE:        '!=';
OR:        '|' | '||';
PLUS:      '+';
SEMICOLON: ';';
LIKE:      '~';
TIMES:     '*';
XOR:       '^';
IMP:       '=>';
EQV:       '<=>';

BOOLEAN:    'true' | 'false';
INTEGER:    DIGIT+;
FLOAT:      [+-]? DIGIT+ DOT DIGIT+ ('e' [+-]? DIGIT+)?;
NEWLINE:    '\r'? '\n';
STRING:     '"' ( ~["\r\n\t] )+? '"' | '\'' ( ~['\r\n\t] )+? '\'' ;
UNICODE:    'u' STRING;
PATTERN:    'r' STRING;
UUID:       '$' STRING;
URL:        'l' STRING;
DATETIME:   't' STRING;

fragment DIGIT:      [0] | NONZERO;
fragment NONZERO:    [1-9];


TYPENAME
    : [A-Z][a-zA-Z0-9]*
    ;

VARNAME
    : [a-z][a-zA-Z0-9_]*
    ;
