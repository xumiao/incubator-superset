grammar norm;

script
    : statement (WSS* statement)* WSS*
    ;

statement
    : comments
    | namespaceExpression WSS* SEMICOLON
    | declarationExpression WSS* SEMICOLON
    | updateExpression WSS* SEMICOLON
    | deleteExpression WSS* SEMICOLON
    | queryExpression WSS* SEMICOLON
    ;

COMMENT: '//' ~[\r\n]*;

comments: '/*' comment_contents '*/' | COMMENT;

comment_contents: ~('*/')+;

namespaceExpression: namespace | imports;

namespace_name: VARNAME (DOT VARNAME)*;

namespace: SPACED_NAMESPACE namespace_name;

SPACED_NAMESPACE: 'namespace' [ \t]*;

imports: SPACED_IMPORT namespace_name (DOT typeName)? (ALS TYPENAME)?;

SPACED_IMPORT: 'import' [ \t]*;

declarationExpression: fullTypeDeclaration | incrementalTypeDeclaration;

typeDefinition: typeName (LBR argumentDeclarations RBR)? (CL typeName)?;

argumentDeclaration: variableName CL typeName;

argumentDeclarations: argumentDeclaration (CA argumentDeclaration)*;

fullTypeDeclaration : typeDefinition AS typeImplementation;

incrementalTypeDeclaration: typeName ORAS typeImplementation;

ORAS : [ \t\u000C]* OR '=' [ \t\u000C\r\n]*;
SOR : [ \u000C]* OR [ \u000C]*;

typeImplementation
    : LCBR code RCBR
    | KERAS_BLOCK code BLOCK_END
    | PYTHON_BLOCK code BLOCK_END
    ;

KERAS_BLOCK : '{%keras';

PYTHON_BLOCK : '{%python';

BLOCK_END : '%}';

code: ~(BLOCK_END)*?;

version: '@' INTEGER (DOT uuid)?;

typeName: TYPENAME version? | 'List' LSBR typeName RSBR | typeName SOR typeName;

variableName : (VARNAME DOT)? (VARNAME | nativeProperty);

querySign: '?' queryLimit?;

queryLimit : INTEGER | '*';

queryProjection: querySign variableName?;

argumentExpressions : argumentExpression (CA argumentExpression)*;

argumentExpression: queryExpression | queryExpression? queryProjection;

SPACED_UPDATE: 'update' [ \t]*;

updateExpression: SPACED_UPDATE queryExpression;

SPACED_DELETE: 'delete' [ \t]*;

deleteExpression: SPACED_DELETE queryExpression;

queryExpression
    : constant
    | variableName
    | LBR queryExpression RBR
    | queryExpression WSS* DOT WSS* (variableName | evaluationExpression)
    | evaluationExpression
    | listExpression
    | sliceExpression
    | arithmeticExpression
    | assignmentExpression
    | conditionExpression
    | NT queryExpression
    | queryExpression spacedLogicalOperator queryExpression
    ;

listExpression : LSBR (queryExpression (CA queryExpression)*)? RSBR;

evaluationExpression: (typeName | variableName) LBR argumentExpressions? RBR queryProjection?;

sliceExpression: (variableName | evaluationExpression | LBR queryExpression RBR) LSBR integer_c? CL integer_c? RSBR;

arithmeticExpression
    : constant
    | listExpression
    | sliceExpression
    | variableName
    | MINUS arithmeticExpression
    | arithmeticExpression spacedArithmeticOperator arithmeticExpression
    | LBR arithmeticExpression RBR
    ;

assignmentExpression: variableName AS queryExpression;

conditionExpression: arithmeticExpression spacedConditionOperator queryExpression;

nativeProperty: 'prob' | 'label' | 'tag' | 'uid' | 'tensor' | 'version';

none: 'none' | 'null' | 'na';

constant
    : none
    | bool_c
    | integer_c
    | float_c
    | string_c
    | unicode_c
    | pattern
    | uuid
    | url
    | datetime
    ;

bool_c:      BOOLEAN;
integer_c:   INTEGER;
float_c:     FLOAT;
string_c:    STRING;
unicode_c:   UNICODE;
pattern:     PATTERN;
uuid:        UUID;
url:         URL;
datetime:    DATETIME;

logicalOperator: AND | OR | XOR | IMP | EQV;

spacedLogicalOperator: WSS? logicalOperator WSS?;

conditionOperator: EQ | NE | IN | NIN | LT | LE | GT | GE | LIKE;

spacedConditionOperator: WSS? conditionOperator WSS?;

arithmeticOperator: PLUS | MINUS | TIMES | DIVIDE | MOD | EXP;

spacedArithmeticOperator: WSS? arithmeticOperator WSS?;

WSS: [ \t\u000C\r\n]+;

LBR: '(' [ \t\u000C\r\n]*;
RBR: [ \t\u000C\r\n]* ')';

LCBR: '{' [ \t\u000C\r\n]*;
RCBR: [ \t\u000C\r\n]* '}';

LSBR: '[' [ \t\u000C\r\n]*;
RSBR: [ \t\u000C\r\n]* ']';

TYPENAME: [A-Z][a-zA-Z0-9]*;

VARNAME: [a-z][a-zA-Z0-9_]*;

NT: NOT [ \t]*;

CA: [ \t\u000C\r\n]* COMMA [ \t\u000C\r\n]*;

CL: [ \t\u000C\r\n]* COLON [ \t\u000C\r\n]*;

AS: [ \t\u000C\r\n]* '=' [ \t\u000C\r\n]*;

ALS: [ \t\u000C\r\n]* 'as' [ \t\u000C\r\n]*;

IN:        'in';
NIN:       '!in';
AND:       '&';
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
OR:        '|';
PLUS:      '+';
SEMICOLON: ';';
LIKE:      '~';
EXP:       '**';
TIMES:     '*';
XOR:       '^';
IMP:       '=>';
EQV:       '<=>';

BOOLEAN:    'true' | 'false';
INTEGER:    [+-]? DIGIT+;
FLOAT:      [+-]? DIGIT+ DOT DIGIT+ ('e' [+-]? DIGIT+)?;
NEWLINE:    '\r'? '\n';
STRING:     '"' ( ~["\r\n\t] )*? '"' | '\'' ( ~['\r\n\t] )*? '\'' ;

UNICODE:   'u' STRING;
PATTERN:   'r' STRING;
UUID:      '$' STRING;
URL:       'l' STRING;
DATETIME:  't' STRING;


fragment DIGIT:      [0] | NONZERO;
fragment NONZERO:    [1-9];


