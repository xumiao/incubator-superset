"""A collection of ORM sqlalchemy models for Lambda"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String, exists
from sqlalchemy.ext.hybrid import hybrid_property

from superset import db
from superset.models.norm import Lambda, Variable

import logging
logger = logging.getLogger(__name__)


class Register(object):
    types = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, cls):
        self.types.append((cls, self.args, self.kwargs))
        return cls

    @classmethod
    def register(cls):
        for clz, args, kwargs in cls.types:
            instance = clz(*args, **kwargs)
            indb = db.session.query(exists().where(clz.signature == instance.signature)).scalar()
            if not indb:
                db.session.add(indb)
        db.session.commit()


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


@Register()
class TypeLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_type'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='Type',
                                           version=1,
                                           description='A logical function',
                                           variables=[])

    @property
    def signature(self):
        return 'Type'


@Register()
class AnyLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_any'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='Any',
                                           version=1,
                                           description='Any type',
                                           variables=[])

    @property
    def signature(self):
        return 'Any'


@Register()
class BooleanLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_boolean'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='Boolean',
                                           version=1,
                                           description='Boolean, true/false, 1/0',
                                           variables=[])

    @property
    def signature(self):
        return 'Boolean'


@Register()
class IntegerLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_integer'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='Integer',
                                           version=1,
                                           description='Integer, -inf..+inf',
                                           variables=[])

    @property
    def signature(self):
        return 'Integer'


@Register()
class StringLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_string'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='String',
                                           version=1,
                                           description='String, "blahbalh"',
                                           variables=[])

    @property
    def signature(self):
        return 'String'


@Register()
class UnicodeLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_unicode'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='Unicode',
                                           version=1,
                                           description='Unicode, u"blahblah"',
                                           variables=[])

    @property
    def signature(self):
        return 'Unicode'


@Register()
class PatternLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_pattern'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='Pattern',
                                           version=1,
                                           description='Pattern, r"^test[0-9]+"',
                                           variables=[])

    @property
    def signature(self):
        return 'Pattern'


@Register()
class UUIDLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_uuid'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='UUID',
                                           version=1,
                                           description='UUID, $"sfsfsfsf"',
                                           variables=[])

    @property
    def signature(self):
        return 'UUID'


@Register()
class URLLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_url'
    }

    def __init__(self):
        super(NativeLambda, self).__init__(name='URL',
                                           version=1,
                                           description='URL, l"http://example.com"',
                                           variables=[])

    @property
    def signature(self):
        return 'URL'


@Register()
class DatetimeLambda(NativeLambda):
    def __init__(self):
        super(NativeLambda, self).__init__(name='Datetime',
                                           version=1,
                                           description='Datetime, t"2018-09-01"',
                                           variables=[])

    @property
    def signature(self):
        return 'Datetime'


@Register(dtype='float32', shape='(300,)')
class TensorLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_tensor'
    }

    dtype = Column(String(16), default='float32')
    shape = Column(String(128), default='(300,)')

    def __init__(self, dtype, shape):
        super(NativeLambda, self).__init__(name='Tensor',
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
