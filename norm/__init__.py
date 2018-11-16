from functools import lru_cache
from textwrap import dedent

from norm.engine import NormCompiler
from norm.executable import NormExecutable


@lru_cache(maxsize=128)
def get_compiler(context_id):
    """
    Get the compiler with respect to the context id
    :param context_id: the id for the context
    :type context_id: int
    :return: a norm compiler
    :rtype: NormCompiler
    """
    return NormCompiler(context_id)


def execute(script, session, user, context_id=None):
    compiler = get_compiler(context_id)
    exe = compiler.compile(dedent(script))
    if isinstance(exe, NormExecutable):
        return exe.execute(session, user, compiler)
    else:
        return exe
