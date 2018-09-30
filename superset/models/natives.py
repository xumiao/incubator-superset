"""A collection of ORM sqlalchemy models for Lambda"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String, exists
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property

from superset import db
from superset.models.norm import Lambda, Variable

import logging
import traceback
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
            indb_query = db.session.query(clz).filter(clz.signature == instance.signature).exists()
            if not db.session.query(indb_query).scalar():
                logger.info('Registering class {}'.format(instance.signature))
                db.session.add(instance)
        try:
            db.session.commit()
        except:
            logger.error('Type registration failed')
            logger.debug(traceback.print_exc())

    @classmethod
    def retrieve(cls, clz, *args, **kwargs):
        instance = clz(*args, **kwargs)
        stored_inst= db.session.query(clz).filter(clz.signature == instance.signature).first()
        if not stored_inst:
            logger.info('Registering class {}'.format(instance.signature))
            db.session.add(instance)
        else:
            instance = stored_inst
        return instance


class NativeLambda(Lambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native'
    }

    def __init__(self, name, version, description, variables):
        super().__init__(namespace='norm.natives',
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
        super().__init__(name='Type',
                         version=1,
                         description='A logical function',
                         variables=[])
        self.signature = 'Type'


@Register()
class AnyLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_any'
    }

    def __init__(self):
        super().__init__(name='Any',
                         version=1,
                         description='Any type',
                         variables=[])
        self.signature = 'Any'


@Register(type_=Register.retrieve(AnyLambda))
class ListLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_list'
    }
    INTERN = 'intern'

    def __init__(self, type_):
        """
        :param type_: the intern type of the list
        :type type_: Lambda
        """
        variable = Variable(self.INTERN, type_)
        super().__init__(name='List',
                         version=1,
                         description='A list of a certain type',
                         variables=[variable])
        self.signature = 'List[{}]'.format(type_.signature)


@Register()
class BooleanLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_boolean'
    }

    def __init__(self):
        super().__init__(name='Boolean',
                         version=1,
                         description='Boolean, true/false, 1/0',
                         variables=[])
        self.signature = 'Boolean'


@Register()
class IntegerLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_integer'
    }

    def __init__(self):
        super().__init__(name='Integer',
                         version=1,
                         description='Integer, -inf..+inf',
                         variables=[])
        self.signature = 'Integer'


@Register()
class StringLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_string'
    }

    def __init__(self):
        super().__init__(name='String',
                         version=1,
                         description='String, "blahbalh"',
                         variables=[])
        self.signature = 'String'


@Register()
class UnicodeLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_unicode'
    }

    def __init__(self):
        super().__init__(name='Unicode',
                         version=1,
                         description='Unicode, u"blahblah"',
                         variables=[])
        self.signature = 'Unicode'


@Register()
class PatternLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_pattern'
    }

    def __init__(self):
        super().__init__(name='Pattern',
                         version=1,
                         description='Pattern, r"^test[0-9]+"',
                         variables=[])
        self.signature = 'Pattern'


@Register()
class UUIDLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_uuid'
    }

    def __init__(self):
        super().__init__(name='UUID',
                         version=1,
                         description='UUID, $"sfsfsfsf"',
                         variables=[])
        self.signature = 'UUID'


@Register()
class URLLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_url'
    }

    def __init__(self):
        super().__init__(name='URL',
                         version=1,
                         description='URL, l"http://example.com"',
                         variables=[])
        self.signature = 'URL'


@Register()
class DatetimeLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_datetime'
    }

    def __init__(self):
        super().__init__(name='Datetime',
                         version=1,
                         description='Datetime, t"2018-09-01"',
                         variables=[])
        self.signature = 'Datetime'


@Register(dtype='float32', shape=[300])
class TensorLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_tensor'
    }

    dtype = Column(String(16), default='float32')
    shape = Column(ARRAY(Integer), default=[300])

    def __init__(self, dtype, shape):
        super().__init__(name='Tensor',
                         version=1,
                         description='Tensor, [2.2, 3.2]',
                         variables=[])
        self.dtype = dtype
        assert(isinstance(shape, list) or isinstance(shape, tuple))
        assert(all([isinstance(element, int) for element in shape]))
        self.shape = list(shape)
        self.signature = 'Tensor[{}]{}'.format(dtype, str(tuple(shape)))

    @hybrid_property
    def dim(self):
        return len(self.shape)

