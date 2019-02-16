from enum import Enum

OMMIT = '...'


class CodeMode(Enum):
    QUERY = ''
    PYTHON = '%python'
    KERAS = '%keras'
    SQL = '%sql'


class AOP(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    EXP = '**'


class COP(Enum):
    GT = '>'
    GE = '>='
    LT = '<'
    LE = '<='
    EQ = '='
    NE = '!='
    LK = '~'
    IN = 'in'
    NI = '!in'


class LOP(Enum):
    AND = 'and'
    OR = 'or'
    XOR = 'xor'
    NOT = 'not'
    IMP = 'imp'
    EQV = 'eqv'


class ConstantType(Enum):
    NULL = 'none'
    BOOL = 'bool'
    INT = 'integer'
    FLT = 'float'
    STR = 'string'
    PTN = 'pattern'
    UID = 'uuid'
    URL = 'url'
    DTM = 'datetime'
    ANY = 'object'


class ImplType(Enum):
    DEF = 'def'
    OR_DEF = 'or_def'
    AND_DEF = 'and_def'
