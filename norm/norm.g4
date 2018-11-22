grammar norm;

script
    : statement (WSS? statement)* WSS?
    ;

statement
    : comments SEMICOLON
    | comments? imports WSS? SEMICOLON
    | comments? namespace? WSS? typeDeclaration WSS? SEMICOLON
    | comments? typeName (WSS? '=' WSS? | WSS? OR '=' WSS? | WSS? AND '=' WSS?) queryExpression WSS? SEMICOLON
    | comments? queryExpression WSS? SEMICOLON
    ;

SINGLELINE: '//' ~[\r\n]* [\r\n]*;
MULTILINE: '/*' (.)*? '*/' [\r\n]*;

comments: MULTILINE | SINGLELINE;

namespace: SPACED_NAMESPACE VARNAME (DOT VARNAME)*;

SPACED_NAMESPACE: 'namespace' [ \t]*;

imports: SPACED_IMPORT VARNAME (DOT VARNAME)* (DOT typeName)? (WSS? AS WSS? VARNAME)?;

SPACED_IMPORT: 'using' [ \t]*;

argumentDeclaration: variableName WSS? COLON WSS? typeName;

argumentDeclarations: argumentDeclaration (WSS? COMMA WSS? argumentDeclaration)*;

typeDeclaration : typeName (LBR argumentDeclarations RBR)? (WSS? COLON WSS? typeName)?;

version: '@' INTEGER?;

typeName
    : VARNAME version?
    | LSBR typeName RSBR;

variableName
    : VARNAME
    | variableName DOT VARNAME;

queryLimit : INTEGER;

queryProjection: '?' queryLimit? variableName?;

argumentExpression
    : OMMIT
    | arithmeticExpression
    | variableName WSS? '=' WSS? arithmeticExpression
    | evaluationExpression
    | variableName WSS? '=' WSS? evaluationExpression
    | queryProjection
    | variableName queryProjection
    | conditionExpression queryProjection?;

argumentExpressions :  argumentExpression (WSS? COMMA WSS? argumentExpression)*;

queryExpression
    : baseQueryExpression queryProjection?
    | sliceExpression queryProjection?
    | chainedExpression queryProjection?
    | LBR queryExpression RBR queryProjection?
    | NT queryExpression
    | queryExpression spacedLogicalOperator queryExpression
    ;

baseQueryExpression
    : arithmeticExpression
    | evaluationExpression
    | codeExpression
    | conditionExpression
    ;

code: ~(KERAS_BLOCK|PYTHON_BLOCK|SQL_BLOCK|BLOCK_END)*;

codeExpression: (KERAS_BLOCK|PYTHON_BLOCK|SQL_BLOCK) code BLOCK_END;

evaluationExpression: typeName LBR argumentExpressions? RBR;

arithmeticExpression
    : constant
    | variableName
    | LBR arithmeticExpression RBR
    | MINUS arithmeticExpression
    | arithmeticExpression spacedArithmeticOperator arithmeticExpression
    ;

conditionExpression: arithmeticExpression spacedConditionOperator arithmeticExpression;

sliceExpression: baseQueryExpression LSBR integer_c? WSS? COLON? WSS? integer_c? RSBR;

chainedExpression
    : baseQueryExpression WSS? DOT WSS? (variableName | evaluationExpression)
    |<assoc=right> chainedExpression WSS? DOT WSS? (variableName | evaluationExpression)
    ;

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
    | ommit
    ;

none:        NONE;
bool_c:      BOOLEAN;
integer_c:   INTEGER;
float_c:     FLOAT;
string_c:    STRING;
unicode_c:   UNICODE;
pattern:     PATTERN;
uuid:        UUID;
url:         URL;
datetime:    DATETIME;
ommit:       OMMIT;

logicalOperator: AND | OR | NOT | XOR | IMP | EQV;

spacedLogicalOperator: WSS? logicalOperator WSS?;

conditionOperator: EQ | NE | IN | NIN | LT | LE | GT | GE | LIKE;

spacedConditionOperator: WSS? conditionOperator WSS?;

arithmeticOperator: PLUS | MINUS | TIMES | DIVIDE | MOD | EXP;

spacedArithmeticOperator: WSS? arithmeticOperator WSS?;

WSS: [ \t\u000C\r\n]+;
NEWLINE: [\r\n]+;

LBR: '(' WSS?;
RBR: WSS? ')';

LCBR: '{' WSS?;
RCBR: WSS? '}';

LSBR: '[' WSS?;
RSBR: WSS? ']';

NONE:      'none' | 'null' | 'na';
AS:        'as';
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
OMMIT:     '..';

BOOLEAN:    'true' | 'false';
INTEGER:    [+-]? DIGIT+;
FLOAT:      [+-]? DIGIT+ DOT DIGIT+ ('e' [+-]? DIGIT+)?;
STRING:     '"' ( ~["\r\n\t] )*? '"' | '\'' ( ~['\r\n\t] )*? '\'' ;

UNICODE:   'u' STRING;
PATTERN:   'r' STRING;
UUID:      '$' STRING;
URL:       'l' STRING;
DATETIME:  't' STRING;

SHOW: '%show' WSS?;
UPDATE: '%update' WSS?;
CREATE: '%create' WSS?;
DELETE: '%delete' WSS?;

KERAS_BLOCK : '{%keras' WSS?;

PYTHON_BLOCK : '{%python' WSS?;

SQL_BLOCK : '{%sql' WSS?;

BLOCK_END : '%}';

NT: NOT [ \t]*;

VARNAME: [a-zA-Z][a-zA-Z0-9_]*;

fragment DIGIT:      [0] | NONZERO;
fragment NONZERO:    [1-9];


