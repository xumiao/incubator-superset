from norm.executable import NormExecutable


class NormExpression(NormExecutable):

    def __init__(self):
        super().__init__()
        self.query = ''

    def execute(self, session, context):
        pass
