grammar norm;

script
    : statement ((WS|NS)? statement)* (WS|NS)?
    ;

statement
    : comments SEMICOLON
    | comments? imports (WS|NS)? SEMICOLON
    | comments? exports (WS|NS)? SEMICOLON
    | comments? (WS|NS)? typeDeclaration (WS|NS)? SEMICOLON
    | comments? typeName (WS|NS)? '=' (WS|NS)? newlineQueryExpression (WS|NS)? SEMICOLON
    | comments? typeName (WS|NS)? OR '=' (WS|NS)? newlineQueryExpression (WS|NS)? SEMICOLON
    | comments? typeName (WS|NS)? AND '=' (WS|NS)? newlineQueryExpression (WS|NS)? SEMICOLON
    | comments? newlineQueryExpression (WS|NS)? SEMICOLON
    ;

SINGLELINE: '//' ~[\r\n]* [\r\n]*;
MULTILINE: '/*' (.)*? '*/' [\r\n]*;

comments: MULTILINE | SINGLELINE;

exports
    : SPACED_EXPORT typeName
    | SPACED_EXPORT typeName (WS|NS)? VARNAME (DOT VARNAME)* ((WS|NS)? AS (WS|NS)? VARNAME)?
    ;

SPACED_EXPORT: 'export' [ \t]*;

imports
    : SPACED_IMPORT VARNAME (DOT VARNAME)* DOT '*'
    | SPACED_IMPORT VARNAME (DOT VARNAME)* DOT typeName ((WS|NS)? AS (WS|NS)? VARNAME)?
    ;

SPACED_IMPORT: 'import' [ \t]*;

argumentDeclaration : variableName (WS|NS)? COLON (WS|NS)? typeName;

argumentDeclarations: argumentDeclaration ((WS|NS)? COMMA (WS|NS)? argumentDeclaration)*;

typeDeclaration : typeName (LBR argumentDeclarations RBR)? ((WS|NS)? COLON (WS|NS)? typeName)?;

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
    | variableName (WS|NS)? '=' (WS|NS)? arithmeticExpression
    | evaluationExpression
    | variableName (WS|NS)? '=' (WS|NS)? evaluationExpression
    | queryProjection
    | variableName queryProjection
    | conditionExpression queryProjection?;

argumentExpressions :  argumentExpression ((WS|NS)? COMMA (WS|NS)? argumentExpression)*;

queryExpression
    : baseQueryExpression queryProjection?
    | sliceExpression queryProjection?
    | chainedExpression queryProjection?
    | LBR queryExpression RBR queryProjection?
    | NOT queryExpression
    | queryExpression spacedLogicalOperator queryExpression
    ;

newlineQueryExpression
    : queryExpression
    | queryExpression newlineLogicalOperator newlineQueryExpression;

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

sliceExpression: baseQueryExpression LSBR integer_c? (WS|NS)? COLON? (WS|NS)? integer_c? RSBR;

chainedExpression
    : baseQueryExpression (WS|NS)? DOT (WS|NS)? (variableName | evaluationExpression)
    |<assoc=right> chainedExpression (WS|NS)? DOT (WS|NS)? (variableName | evaluationExpression)
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

spacedLogicalOperator: WS? logicalOperator WS?;

newlineLogicalOperator: NS logicalOperator WS?;

conditionOperator: EQ | NE | IN | NIN | LT | LE | GT | GE | LIKE;

spacedConditionOperator: (WS|NS)? conditionOperator (WS|NS)?;

arithmeticOperator: PLUS | MINUS | TIMES | DIVIDE | MOD | EXP;

spacedArithmeticOperator: (WS|NS)? arithmeticOperator (WS|NS)?;

WS: [ \t\u000C]+ -> skip;

NS: [ \t\u000C]+ [\r\n] [ \t\u000C]* | [\r\n] [ \t\u000C]*;

LBR: '(' (WS|NS)?;
RBR: (WS|NS)? ')';

LCBR: '{' (WS|NS)?;
RCBR: (WS|NS)? '}';

LSBR: '[' (WS|NS)?;
RSBR: (WS|NS)? ']';

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
OMMIT:     '...';

BOOLEAN:    'true' | 'false';
INTEGER:    [+-]? DIGIT+;
FLOAT:      [+-]? DIGIT+ DOT DIGIT+ ('e' [+-]? DIGIT+)?;
STRING:     '"' ( ~["\r\n\t] )*? '"' | '\'' ( ~['\r\n\t] )*? '\'' ;

UNICODE:   'u' STRING;
PATTERN:   'r' STRING;
UUID:      '$' STRING;
URL:       'l' STRING;
DATETIME:  't' STRING;

SHOW: '%show' (WS|NS)?;
UPDATE: '%update' (WS|NS)?;
CREATE: '%create' (WS|NS)?;
DELETE: '%delete' (WS|NS)?;

KERAS_BLOCK : '{%keras' (WS|NS)?;

PYTHON_BLOCK : '{%python' (WS|NS)?;

SQL_BLOCK : '{%sql' (WS|NS)?;

BLOCK_END : '%}';

NT: NOT [ \t]*;

VARNAME: [a-zA-Z][a-zA-Z0-9_]*;

fragment DIGIT:      [0] | NONZERO;
fragment NONZERO:    [1-9];


