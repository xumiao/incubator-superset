"""A collection of ORM sqlalchemy models for Lambda"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from textwrap import dedent

from future.standard_library import install_aliases

from flask_appbuilder import Model

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy import Table
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy.orm import relationship, with_polymorphic

from superset import app, utils
from superset import security_manager as sm

from superset.models.helpers import AuditMixinNullable
from superset.models.mixins import VersionedMixin, lazy_property, ParametrizedMixin
from superset.models.core import metadata

from pandas import DataFrame
import pandas as pd

import traceback
import logging
logger = logging.getLogger(__name__)

install_aliases()

config = app.config


class Variable(Model, ParametrizedMixin):
    """Variable placeholder"""

    __tablename__ = 'variables'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), default='')
    as_input = Column(Boolean, default=True)
    as_output = Column(Boolean, default=True)
    type_id = Column(Integer, ForeignKey('lambdas.id'))
    type_ = relationship('Lambda', foreign_keys=[type_id])

    def __init__(self, name, type_, as_input=True, as_output=True):
        """
        Construct the variable
        :param name: the full name of the variable
        :type name: str
        :param type_: the type of the variable
        :type type_: Lambda
        """
        self.name = name
        self.type_ = type_
        self.as_input = as_input
        self.as_output = as_output


lambda_user = Table(
    'lambda_user', metadata,
    Column('id', Integer, primary_key=True),
    Column('lambda_id', Integer, ForeignKey('lambdas.id')),
    Column('user_id', Integer, ForeignKey('ab_user.id')),
)

lambda_variable = Table(
    'lambda_variable', metadata,
    Column('id', Integer, primary_key=True),
    Column('lambda_id', Integer, ForeignKey('lambdas.id')),
    Column('variable_id', Integer, ForeignKey('variables.id'))
)


class Lambda(Model, AuditMixinNullable, VersionedMixin, ParametrizedMixin):
    """Lambda model is a function"""

    __tablename__ = 'lambdas'
    signature = Column(String(1024), nullable=False)
    description = Column(Text, default='')
    perm = Column(String(1024))
    code = Column(Text, default='')
    category = Column(String(128))
    owners = relationship(sm.user_model, secondary=lambda_user)
    variables = relationship(Variable, secondary=lambda_variable)

    __mapper_args__ = {
        'polymorphic_identity': 'lambda',
        'polymorphic_on': category
    }

    def __init__(self, namespace='', name='', version=None, description='', params='', code='',
                 variables=None, user=None):
        super().__init__(namespace=namespace, name=name, version=version)
        self.description = description
        self.params = params
        self.code = code
        if user:
            self.creator = user
            self.owners = [user]
        if variables is None:
            self.variables = []
        else:
            self.variables = variables
        self.signature = self.fully_qualified_name

    @hybrid_property
    def nargs(self):
        return len(self.variables)

    def clone(self, user=None):
        """
         Clone a Lambda
         :return: the cloned version of the Lambda
         :rtype: Lambda
         """
        return self.__class__(namespace=self.namespace,
                              name=self.name,
                              description=self.description,
                              params=self.params,
                              code=self.code,
                              variables=self.variables,
                              user=user or self.creator)

    @property
    def description_markeddown(self):
        return utils.markdown(self.description)

    def __call__(self, *args, **kwargs):
        """
        TODO: implement
        """
        pass

    @property
    def data_file(self):
        root = config.get('DATA_STORAGE_ROOT')
        return '{}/{}/{}.parquet'.format(root, self.namespace, self.name)

    def query(self, filters=None, projections=None):
        if projections is None:
            df = pd.read_parquet(self.data_file)
        else:
            df = pd.read_parquet(self.data_file, columns=[col[0] for col in projections])
            df = df.rename(columns=dict(projections))
        if filters:
            projections = dict(projections)
            from norm.literals import COP
            for col, op, value in filters:
                pcol = projections.get(col, col)
                df = df[df[pcol].notnull()]
                if op == COP.LK:
                    df = df[df[pcol].str.contains(value.value)]
                elif op == COP.GT:
                    df = df[df[pcol] > value.value]
                elif op == COP.GE:
                    df = df[df[pcol] >= value.value]
                elif op == COP.LT:
                    df = df[df[pcol] < value.value]
                elif op == COP.LE:
                    df = df[df[pcol] <= value.value]
                elif op == COP.EQ:
                    df = df[df[pcol] == value.value]
                elif op == COP.NE:
                    if value.value is not None:
                        df = df[df[pcol] != value.value]
                elif op == COP.IN:
                    # TODO: Wrong
                    df = df[df[pcol].isin(value.value)]
                elif op == COP.NI:
                    # TODO: Wrong
                    df = df[~df[pcol].isin(value.value)]
        return df

    def set_values(self, mem, variable_name, values):
        """
        Set values of current type to the memory by the variable name
        :param mem: the memory to store the values
        :type mem: DataFrame
        :param variable_name: the variable name
        :type variable_name: str
        :param values: the values to store in the memory
        :type values: DataFrame
        """
        pass

    def get_values(self, mem, variable_name):
        """
        Get values of current type to the memory by the variable name
        :param mem: the memory to store the values
        :type mem: DataFrame
        :param variable_name: the variable name
        :type variable_name: str
        """
        pass


class KerasLambda(Lambda):

    __mapper_args__ = {
        'polymorphic_identity': 'lambda_keras'
    }

    def __init__(self, namespace='', name='', version=None, description='', params='', code='',
                 variables=None, user=None):
        super().__init__(namespace=namespace, name=name, version=version, description=description, params=params,
                         code=code, variables=variables, user=user)

    @lazy_property
    def keras_model(self):
        return None

    def __call__(self, *args, **kwargs):
        """
        TODO: implement
        """
        pass


class PythonLambda(Lambda):
    APPLY_FUNC_NAME = 'apply'

    __mapper_args__ = {
        'polymorphic_identity': 'lambda_python'
    }

    def __init__(self, namespace='', name='', version=None, description='', params='', code='',
                 variables=None, user=None):
        super().__init__(namespace=namespace, name=name, version=version, description=description, params=params,
                         code=code, variables=variables, user=user)

    @lazy_property
    def apply_func(self):
        try:
            d = {}
            exec(dedent(self.code), d)
            return d.get(self.APPLY_FUNC_NAME)  # Should fail if the definition does not exist
        except:
            msg = 'Can not load apply function for {} : {} '.format(str(self), self.code)
            logger.error(msg)
            logger.debug(traceback.print_exc())
            raise RuntimeError(msg)

    def __call__(self, *args, **kwargs):
        """
        TODO: implement
        """
        pass


def retrieve_type(namespace, name, version, session):
    """
    Retrieving a Lambda
    :type namespace: basestring
    :type name: basestring
    :type version: int
    :type session: sqlalchemy.orm.Session
    :return: the Lambda or None
    """
    if version:
        lam = session.query(with_polymorphic(Lambda, '*'))\
            .filter(Lambda.name == name, Lambda.version == version) \
            .first()
    else:
        lam = session.query(with_polymorphic(Lambda, '*')) \
            .filter(Lambda.name == name) \
            .first()
    return lam
