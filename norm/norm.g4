grammar norm;

script
    : statement (WSS? statement)* WSS?
    ;

statement
    : (comments)? namespaceExpression WSS? SEMICOLON
    | (comments)? namespace? WSS? typeDeclaration WSS? SEMICOLON
    | (comments)? queryExpression WSS? SEMICOLON
    | (comments)? typeName (ASS | ORAS | ANDAS) queryExpression WSS? SEMICOLON
    ;

COMMENT: '#' ~[\r\n]* NEWLINE;

comments: '/*' comment_contents '*/' NEWLINE | COMMENT;

comment_contents: ~('*/')+;

namespaceExpression: namespace | imports;

namespace_name: VARNAME (DOT VARNAME)*;

namespace: SPACED_NAMESPACE namespace_name;

SPACED_NAMESPACE: 'namespace' [ \t]*;

imports: SPACED_IMPORT namespace_name (DOT typeName)? (ALS TYPENAME)?;

SPACED_IMPORT: 'import' [ \t]*;

argumentDeclaration: variableName CL typeName;

argumentDeclarations: argumentDeclaration (CA argumentDeclaration)*;

typeDeclaration : typeName (LBR argumentDeclarations RBR)? (CL typeName)?;

magic_command
    : SHOW
    | CREATE
    | UPDATE
    | DELETE
    ;

version: '@' INTEGER?;

typeName: TYPENAME version? | 'List' LSBR typeName RSBR | typeName OR typeName;

variableName : VARNAME | nativeProperty;

querySign: '?' queryLimit?;

queryLimit : INTEGER;

queryProjection: querySign variableName?;

argumentExpression
    : '*'
    | arithmeticExpression
    | variableName ASS arithmeticExpression
    | queryProjection
    | variableName queryProjection
    | conditionExpression queryProjection?;

argumentExpressions : argumentExpression (CA argumentExpression)*;

queryExpression
    : constant queryProjection?
    | codeExpression queryProjection?
    | evaluationExpression queryProjection?
    | sliceExpression queryProjection?
    | chainedExpression queryProjection?
    | arithmeticExpression queryProjection
    | conditionExpression
    | LBR queryExpression RBR
    | NT queryExpression
    | queryExpression spacedLogicalOperator queryExpression
    ;

code: ~(KERAS_BLOCK|PYTHON_BLOCK|SQL_BLOCK|BLOCK_END)*;

codeExpression: (KERAS_BLOCK|PYTHON_BLOCK|SQL_BLOCK) code BLOCK_END;

evaluationExpression: typeName LBR argumentExpressions? RBR;

sliceExpression: typeName LSBR integer_c? CL integer_c? RSBR;

chainedExpression
    : evaluationExpression WSS? DOT WSS? (variableName | evaluationExpression)
    |<assoc=right> chainedExpression WSS? DOT WSS? (variableName | evaluationExpression)
    ;

arithmeticExpression
    : constant
    | variableName
    | LBR arithmeticExpression RBR
    | MINUS arithmeticExpression
    | arithmeticExpression spacedArithmeticOperator arithmeticExpression
    ;

conditionExpression: arithmeticExpression spacedConditionOperator arithmeticExpression;

nativeProperty: 'prob' | 'label' | 'tag' | 'uid' | 'tensor' | 'version';

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

logicalOperator: AND | OR | NOT | XOR | IMP | EQV;

spacedLogicalOperator: WSS? logicalOperator WSS?;

conditionOperator: EQ | NE | IN | NIN | LT | LE | GT | GE | LIKE;

spacedConditionOperator: WSS? conditionOperator WSS?;

arithmeticOperator: PLUS | MINUS | TIMES | DIVIDE | MOD | EXP;

spacedArithmeticOperator: WSS? arithmeticOperator WSS?;

WSS: [ \t\u000C\r\n]+;

LBR: '(' WSS?;
RBR: WSS? ')';

LCBR: '{' WSS?;
RCBR: WSS? '}';

LSBR: '[' WSS?;
RSBR: WSS? ']';

NONE:      'none' | 'null' | 'na';
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

SHOW: '%show' WSS?;
UPDATE: '%update' WSS?;
CREATE: '%create' WSS?;
DELETE: '%delete' WSS?;

KERAS_BLOCK : '{%keras' WSS?;

PYTHON_BLOCK : '{%python' WSS?;

SQL_BLOCK : '{%sql' WSS?;

BLOCK_END : '%}';

ORAS : WSS? OR '=' WSS?;

ANDAS : WSS? AND '=' WSS?;

NT: NOT [ \t]*;

CA: WSS? COMMA WSS?;

CL: WSS? COLON WSS?;

ASS: WSS? '=' WSS?;

ALS: WSS? 'as' WSS?;

TYPENAME: [A-Z][a-zA-Z0-9]*;

VARNAME: [a-z][a-zA-Z0-9_]*;

fragment DIGIT:      [0] | NONZERO;
fragment NONZERO:    [1-9];


