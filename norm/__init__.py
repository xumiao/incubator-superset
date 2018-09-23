from norm.engine import NormCompiler

compiler = NormCompiler()


def execute(script, session, user, context=None):
    executable = compiler.compile(script)
    return executable.execute(context, session, user)
