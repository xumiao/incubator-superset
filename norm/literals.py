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


class COP(Enum):
    GT = '>'
    GE = '>='
    LT = '<'
    LE = '<='
    EQ = '=='
    NE = '!='
    LK = '~'
    IN = 'in'
    NI = '!in'


class LOP(Enum):
    AND = '&'
    OR = '|'
    NOT = '!'
    IMP = '=>'
    EQV = '<=>'


class ConstantType(Enum):
    NULL = 'none'
    BOOL = 'bool'
    INT = 'integer'
    FLT = 'float'
    STR = 'string'
    UNC = 'unicode'
    PTN = 'pattern'
    UID = 'uuid'
    URL = 'url'
    DTM = 'datetime'


class ImplType(Enum):
    ASS = 'assign'
    ORAS = 'or_assign'
    ANDAS = 'and_assign'
