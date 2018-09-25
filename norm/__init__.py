from norm.engine import NormCompiler

compiler = NormCompiler()


def execute(script, session, user):
    executable = compiler.compile(script)
    return executable.execute(session, user)
