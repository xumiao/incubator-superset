grammar norm;

script: statement ((WS|NS)? statement)* (WS|NS)?;

statement
    : comments SEMICOLON
    | comments? imports (WS|NS)? SEMICOLON
    | comments? exports (WS|NS)? SEMICOLON
    | comments? (WS|NS)? typeDeclaration (WS|NS)? SEMICOLON
    | comments? typeName (WS|NS)? '=' (WS|NS)? multiLineExpression (WS|NS)? SEMICOLON
    | comments? typeName (WS|NS)? OR '=' (WS|NS)? multiLineExpression (WS|NS)? SEMICOLON
    | comments? typeName (WS|NS)? AND '=' (WS|NS)? multiLineExpression (WS|NS)? SEMICOLON
    | comments? multiLineExpression (WS|NS)? SEMICOLON
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

argumentDeclaration : VARNAME (WS|NS)? COLON (WS|NS)? typeName;

argumentDeclarations: argumentDeclaration ((WS|NS)? COMMA (WS|NS)? argumentDeclaration)*;

typeDeclaration : typeName (LBR argumentDeclarations RBR)? ((WS|NS)? COLON (WS|NS)? typeName)?;

version: '@' INTEGER?;

typeName
    : VARNAME version?
    | LSBR typeName RSBR;

variableExpression
    : VARNAME
    | '_' LBR variableExpression RBR
    | VARNAME DOT variableExpression
    | LBR variableExpression (COMMA variableExpression)* RBR
    ;

queryLimit : INTEGER;

queryProjection : '?' queryLimit? variableExpression?;

argumentExpression
    : arithmeticExpression
    | VARNAME (WS|NS)? '=' (WS|NS)? arithmeticExpression
    | VARNAME spacedConditionOperator arithmeticExpression
    | queryProjection
    | VARNAME queryProjection
    | argumentExpression queryProjection
    ;

argumentExpressions
    : LBR RBR
    | LBR argumentExpression ((WS|NS)? COMMA (WS|NS)? argumentExpression)* RBR
    ;

constant
    : none
    | bool_c
    | integer_c
    | float_c
    | string_c
    | pattern
    | uuid
    | url
    | datetime
    | LSBR constant (COMMA constant)* RSBR
    ;

code: ~(PYTHON_BLOCK|SQL_BLOCK|BLOCK_END)*;

codeExpression: (PYTHON_BLOCK|SQL_BLOCK) code BLOCK_END;

evaluationExpression
    : constant
    | codeExpression
    | VARNAME argumentExpressions?
    | VARNAME argumentExpressions? (WS|NS)? DOT (WS|NS)? evaluationExpression
    ;

slicedExpression
    : evaluationExpression
    | evaluationExpression LSBR integer_c? (WS|NS)? COLON? (WS|NS)? integer_c? RSBR
    | evaluationExpression LSBR evaluationExpression RSBR
    ;

arithmeticExpression
    : slicedExpression
    | LBR arithmeticExpression RBR
    | MINUS arithmeticExpression
    | arithmeticExpression (WS|NS)? (MOD | EXP) (WS|NS)? arithmeticExpression
    | arithmeticExpression (WS|NS)? (TIMES | DIVIDE) (WS|NS)? arithmeticExpression
    | arithmeticExpression (WS|NS)? (PLUS | MINUS) (WS|NS)? arithmeticExpression
    ;

conditionExpression
    : arithmeticExpression
    | arithmeticExpression spacedConditionOperator arithmeticExpression
    ;

oneLineExpression
    : conditionExpression queryProjection?
    | LBR oneLineExpression RBR queryProjection?
    | NOT WS? oneLineExpression
    | oneLineExpression spacedLogicalOperator oneLineExpression
    ;

multiLineExpression
    : oneLineExpression
    | oneLineExpression newlineLogicalOperator multiLineExpression
    ;


none:        NONE;
bool_c:      BOOLEAN;
integer_c:   INTEGER;
float_c:     FLOAT;
string_c:    STRING;
pattern:     PATTERN;
uuid:        UUID;
url:         URL;
datetime:    DATETIME;

logicalOperator: AND | OR | NOT | XOR | IMP | EQV;

spacedLogicalOperator: WS? logicalOperator WS?;

newlineLogicalOperator: NS logicalOperator WS?;

conditionOperator: EQ | NE | IN | NIN | LT | LE | GT | GE | LIKE;

spacedConditionOperator: (WS|NS)? conditionOperator (WS|NS)?;

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
COLON:     ':';
SEMICOLON: ';';
COMMA:     ',';
DOT:       '.';
DOTDOT:    '..';

IN:        'in';
NIN:       '!in';
EQ:        '==';
NE:        '!=';
GE:        '>=';
LE:        '<=';
GT:        '>';
LT:        '<';
LIKE:      '~';

MINUS:     '-';
PLUS:      '+';
TIMES:     '*';
DIVIDE:    '/';
EXP:       '**';
MOD:       '%';

NOT:       '!' | 'not';
AND:       '&' | 'and';
OR:        '|' | 'or';
XOR:       '^' | 'xor';
IMP:       '=>' | 'imp';
EQV:       '<=>' | 'eqv';

BOOLEAN:    'true' | 'false' | 'True' | 'False';
INTEGER:    [+-]? DIGIT+;
FLOAT:      [+-]? DIGIT+ DOT DIGIT+ ('e' [+-]? DIGIT+)?;
STRING:     '"' ( ~["\r\n\t] )*? '"' | '\'' ( ~['\r\n\t] )*? '\'' ;

PATTERN:   'r' STRING;
UUID:      '$' STRING;
URL:       'l' STRING;
DATETIME:  't' STRING;

SHOW: '%show' (WS|NS)?;
DELETE: '%delete' (WS|NS)?;

PYTHON_BLOCK : '{%python' (WS|NS)?;
SQL_BLOCK : '{%sql' (WS|NS)?;
BLOCK_END : '%}';

VARNAME: [a-zA-Z][a-zA-Z0-9_]*;

fragment DIGIT:      [0] | NONZERO;
fragment NONZERO:    [1-9];


