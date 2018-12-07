"""A collection of ORM sqlalchemy models for Lambda"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String, exists
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property

from norm.config import db
from norm.models.norm import Lambda, Variable, Status

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
            in_store = db.session.query(exists().where(clz.name == instance.name)).scalar()
            if not in_store:
                logger.info('Registering class {}'.format(instance.name))
                db.session.add(instance)
        try:
            db.session.commit()
        except:
            logger.error('Type registration failed')
            logger.debug(traceback.print_exc())

    @classmethod
    def retrieve(cls, clz, *args, **kwargs):
        instance = clz(*args, **kwargs)
        stored_inst = db.session.query(clz).filter(clz.name == instance.name).scalar()
        if stored_inst is None:
            stored_inst = instance
            db.session.add(instance)
        return stored_inst


class NativeLambda(Lambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native'
    }
    NAMESPACE = 'norm.native'

    def __init__(self, name, description, variables):
        super().__init__(namespace=self.NAMESPACE,
                         name=name,
                         description=description,
                         variables=variables)
        self.status = Status.READY

    def load_data(self):
        """
        Native lambdas do not have data
        :return: None
        """
        return None


@Register()
class TypeLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_type'
    }

    def __init__(self):
        super().__init__(name='Type',
                         description='A logical function',
                         variables=[])


@Register()
class AnyLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_any'
    }

    def __init__(self):
        super().__init__(name='Any',
                         description='Any type',
                         variables=[])


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
        super().__init__(name='List[{}]'.format(type_.signature),
                         description='A list of a certain type',
                         variables=[variable])


@Register()
class BooleanLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_boolean'
    }

    def __init__(self):
        super().__init__(name='Boolean',
                         description='Boolean, true/false, 1/0',
                         variables=[])


@Register()
class IntegerLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_integer'
    }

    def __init__(self):
        super().__init__(name='Integer',
                         description='Integer, -inf..+inf',
                         variables=[])


@Register()
class StringLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_string'
    }

    def __init__(self):
        super().__init__(name='String',
                         description='String, "blahbalh"',
                         variables=[])


@Register()
class UnicodeLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_unicode'
    }

    def __init__(self):
        super().__init__(name='Unicode',
                         description='Unicode, u"blahblah"',
                         variables=[])


@Register()
class PatternLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_pattern'
    }

    def __init__(self):
        super().__init__(name='Pattern',
                         description='Pattern, r"^test[0-9]+"',
                         variables=[])


@Register()
class UUIDLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_uuid'
    }

    def __init__(self):
        super().__init__(name='UUID',
                         description='UUID, $"sfsfsfsf"',
                         variables=[])


@Register()
class URLLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_url'
    }

    def __init__(self):
        super().__init__(name='URL',
                         description='URL, l"http://example.com"',
                         variables=[])


@Register()
class DatetimeLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_datetime'
    }

    def __init__(self):
        super().__init__(name='Datetime',
                         description='Datetime, t"2018-09-01"',
                         variables=[])


@Register(dtype='float32', shape=[300])
class TensorLambda(NativeLambda):
    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native_tensor'
    }

    dtype = Column(String(16), default='float32')
    shape = Column(ARRAY(Integer), default=[300])

    def __init__(self, dtype, shape):
        super().__init__(name='Tensor[{}]{}'.format(dtype, str(tuple(shape))),
                         description='Tensor, [2.2, 3.2]',
                         variables=[])
        self.dtype = dtype
        assert(isinstance(shape, list) or isinstance(shape, tuple))
        assert(all([isinstance(element, int) for element in shape]))
        self.shape = list(shape)

    @hybrid_property
    def dim(self):
        return len(self.shape)

