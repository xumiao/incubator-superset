"""A collection of ORM sqlalchemy models for Lambda"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property

from superset import app, db
from superset.models.norm import Lambda, Variable

import traceback
import logging
logger = logging.getLogger(__name__)


class NativeLambda(Lambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native'
    }

    def __init__(self, name, version, description, variables):
        super(Lambda, self).__init__(namespace='norm.natives',
                                     name=name,
                                     version=version,
                                     description=description,
                                     variables=variables)


class TypeLambda(NativeLambda):
    """
    A Type relation returns a Lambda object
    """

    def __init__(self):
        super(TypeLambda, self).__init__(name='Type',
                                         version=1,
                                         description='A logical function',
                                         variables=[])

    @property
    def signature(self):
        return 'Type'


class BooleanLambda(NativeLambda):
    def __init__(self):
        super(BooleanLambda, self).__init__(name='Boolean',
                                            version=1,
                                            description='Boolean, true/false, 1/0',
                                            variables=[])

    @property
    def signature(self):
        return 'Boolean'


class IntegerLambda(NativeLambda):
    def __init__(self):
        super(IntegerLambda, self).__init__(name='Integer',
                                            version=1,
                                            description='Integer, -inf..+inf',
                                            variables=[])

    @property
    def signature(self):
        return 'Integer'


class StringLambda(NativeLambda):
    def __init__(self):
        super(StringLambda, self).__init__(name='String',
                                           version=1,
                                           description='String, "blahbalh"',
                                           variables=[])

    @property
    def signature(self):
        return 'String'


class UnicodeLambda(NativeLambda):
    def __init__(self):
        super(UnicodeLambda, self).__init__(name='Unicode',
                                            version=1,
                                            description='Unicode, u"blahblah"',
                                            variables=[])

    @property
    def signature(self):
        return 'Unicode'


class PatternLambda(NativeLambda):
    def __init__(self):
        super(PatternLambda, self).__init__(name='Pattern',
                                            version=1,
                                            description='Pattern, r"^test[0-9]+"',
                                            variables=[])

    @property
    def signature(self):
        return 'Pattern'


class UUIDLambda(NativeLambda):
    def __init__(self):
        super(UUIDLambda, self).__init__(name='UUID',
                                         version=1,
                                         description='UUID, $"sfsfsfsf"',
                                         variables=[])

    @property
    def signature(self):
        return 'UUID'


class URLLambda(NativeLambda):
    def __init__(self):
        super(URLLambda, self).__init__(name='URL',
                                        version=1,
                                        description='URL, l"http://example.com"',
                                        variables=[])

    @property
    def signature(self):
        return 'URL'


class DatetimeLambda(NativeLambda):
    def __init__(self):
        super(DatetimeLambda, self).__init__(name='Datetime',
                                             version=1,
                                             description='Datetime, t"2018-09-01"',
                                             variables=[])

    @property
    def signature(self):
        return 'Datetime'


class AnyLambda(NativeLambda):
    def __init__(self):
        super(AnyLambda, self).__init__(name='Any',
                                        version=1,
                                        description='Any type',
                                        variables=[])

    @property
    def signature(self):
        return 'Any'


class TensorLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_tensor'
    }

    dtype = Column(String(16), default='float32')
    shape = Column(String(128), default='(300,')

    def __init__(self, dtype, shape):
        super(TensorLambda, self).__init__(name='Tensor',
                                           version=1,
                                           description='Tensor, [2.2, 3.2]',
                                           variables=[])
        self.dtype = dtype
        self.shape = str(shape)

    @hybrid_property
    def dim(self):
        return len(eval(self.shape))

    @property
    def signature(self):
        return 'Tensor[{}]{}'.format(self.dtype, self.shape)
