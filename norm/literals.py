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
    EQ = '=='
    NE = '!='
    LK = '~'
    IK = '~~'
    IN = 'in'
    NI = '!in'


class LOP(Enum):
    AND = '&'
    OR = '|'
    NOT = '!'
    IMP = '=>'
    EQV = '<=>'


class ROP(Enum):
    ASS = '='


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
